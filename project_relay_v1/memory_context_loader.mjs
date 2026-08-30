#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const RULES = JSON.parse(fs.readFileSync(path.join(HERE, 'memory_rules_v1.json'), 'utf8'));
export const VERSION = `memory-context-js-${RULES.version}`;
export const DEFAULT_MAX_DOCS = Number(RULES.defaults?.max_docs ?? 8);
export const DEFAULT_CHAR_BUDGET = Number(RULES.defaults?.char_budget ?? 24000);

const norm = (text) => String(text ?? '').trim().toLowerCase().replace(/\s+/g, ' ');
const splitCsv = (value) => {
  if (!value) return new Set();
  if (Array.isArray(value)) return new Set(value.map(String).map(v => v.trim()).filter(Boolean));
  return new Set(String(value).split(',').map(v => v.trim()).filter(Boolean));
};

export function classifyTask(instruction) {
  const text = norm(instruction);
  const scored = [];
  for (const rule of RULES.task_rules) {
    const hits = rule.keywords.filter(kw => text.includes(String(kw).toLowerCase()));
    if (hits.length) scored.push([hits.length * Number(rule.weight), rule.task_kind, hits]);
  }

  let taskKind = 'GENERAL';
  let taskHits = [];
  let confidence = 0.35;
  if (scored.length) {
    scored.sort((a, b) => b[0] - a[0] || String(b[1]).localeCompare(String(a[1])));
    [, taskKind, taskHits] = scored[0];
    if (taskKind === 'RESEARCH_SUMMARY' && ['歴史', '変遷', '起源', '発展'].some(k => text.includes(k))) {
      taskKind = 'HISTORICAL_RESEARCH';
    }
    confidence = Math.min(0.99, 0.60 + 0.08 * taskHits.length);
  }

  const domains = [];
  for (const [domain, keywords] of Object.entries(RULES.domain_rules)) {
    if (keywords.some(kw => text.includes(String(kw).toLowerCase()))) domains.push(domain);
  }
  if (['HISTORICAL_RESEARCH', 'RESEARCH_SUMMARY'].includes(taskKind)) {
    domains.push('research');
    if (taskKind === 'HISTORICAL_RESEARCH') domains.push('history');
  }

  return {
    classifier_version: VERSION,
    rules_version: RULES.version,
    task_focus: String(instruction ?? '').trim(),
    task_kind: taskKind,
    domains: [...new Set(domains)].sort(),
    confidence,
    matched_keywords: taskHits,
  };
}

function relevance(doc, taskKind, domains, missionKey) {
  if (doc.status !== 'ACTIVE') return [-1, ['inactive']];
  const policy = doc.load_policy ?? 'WHEN_DOMAIN';
  const reasons = [];
  let score = 0;

  if (policy === 'MANUAL_ONLY') return [-1, ['manual-only']];
  if (policy === 'ALWAYS') { score += 10000; reasons.push('ALWAYS'); }

  const docMission = String(doc.mission_key ?? '');
  if (missionKey && docMission === missionKey) { score += 9000; reasons.push('mission-exact'); }
  else if (policy === 'WHEN_MISSION' && docMission) return [-1, ['other-mission']];

  const taskKinds = splitCsv(doc.task_kinds);
  if (taskKinds.has('ALL')) { score += 500; reasons.push('task-all'); }
  else if (taskKinds.has(taskKind)) { score += 6000; reasons.push('task-kind'); }
  else if (policy === 'WHEN_TASK_KIND') return [-1, ['task-mismatch']];

  const docDomains = splitCsv(doc.domains);
  if (docDomains.has('ALL')) { score += 300; reasons.push('domain-all'); }
  else {
    const overlap = [...domains].filter(d => docDomains.has(d)).sort();
    if (overlap.length) { score += 2500 + 200 * overlap.length; reasons.push(`domain:${overlap.join(',')}`); }
    else if (policy === 'WHEN_DOMAIN') return [-1, ['domain-mismatch']];
  }

  const priority = Number(doc.priority ?? 50);
  score += Math.max(0, 200 - priority);
  if (doc.required) { score += 500; reasons.push('required'); }
  return [score, reasons];
}

export function selectContext(instruction, catalog, options = {}) {
  const projectKey = options.project_key ?? 'project_relay';
  const missionKey = options.mission_key ?? '';
  const maxDocs = Number(options.max_docs ?? DEFAULT_MAX_DOCS);
  const charBudget = Number(options.char_budget ?? DEFAULT_CHAR_BUDGET);
  const task = classifyTask(instruction);
  const domains = new Set(task.domains);
  const candidates = [];
  const excluded = [];

  for (const doc of catalog) {
    if (![projectKey, '*'].includes(doc.project_key)) {
      excluded.push({ memory_key: doc.memory_key ?? '?', reason: 'project-mismatch' });
      continue;
    }
    const [score, reasons] = relevance(doc, task.task_kind, domains, missionKey);
    if (score < 0) {
      excluded.push({ memory_key: doc.memory_key ?? '?', reason: reasons.join(';') });
      continue;
    }
    candidates.push([score, doc, reasons]);
  }

  candidates.sort((a, b) => b[0] - a[0] || Number(a[1].priority ?? 50) - Number(b[1].priority ?? 50) || String(a[1].memory_key).localeCompare(String(b[1].memory_key)));
  const selected = [];
  let usedChars = 0;
  for (const [score, doc, reasons] of candidates) {
    if (selected.length >= maxDocs) {
      excluded.push({ memory_key: doc.memory_key, reason: 'max-docs-budget' });
      continue;
    }
    const size = Number(doc.estimated_chars ?? 0);
    if (selected.length && usedChars + size > charBudget) {
      excluded.push({ memory_key: doc.memory_key, reason: 'char-budget' });
      continue;
    }
    selected.push({
      memory_key: doc.memory_key,
      title: doc.title ?? '',
      drive_file_id: doc.drive_file_id ?? '',
      drive_file_url: doc.drive_file_url ?? '',
      estimated_chars: size,
      score,
      reasons,
    });
    usedChars += size;
  }

  return {
    ...task,
    project_key: projectKey,
    mission_key: missionKey,
    max_docs: maxDocs,
    char_budget: charBudget,
    selected_doc_count: selected.length,
    estimated_chars: usedChars,
    selected,
    selected_memory_keys: selected.map(d => d.memory_key),
    excluded,
    status: 'SELECTED',
  };
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const [instruction = '', catalogPath = '', missionKey = ''] = process.argv.slice(2);
  if (!catalogPath) {
    console.error('Usage: memory_context_loader.mjs <instruction> <catalog.json> [mission_key]');
    process.exit(2);
  }
  const catalog = JSON.parse(fs.readFileSync(catalogPath, 'utf8'));
  console.log(JSON.stringify(selectContext(instruction, catalog, { mission_key: missionKey }), null, 2));
}
