// P1_VtableDispatchMap.java
// CSMC P1: exact vtable dispatch mapper.
// Scope is deliberately bounded: two known loader vtables, 9 slots each,
// plus one precheck RVA. Existing snapshot decompiles are NOT decompiled again.

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSetView;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.regex.*;

public class P1_VtableDispatchMap extends GhidraScript {
    private static final Pattern TARGET_LINE =
        Pattern.compile("^([^\\t#]+)\\t(0x[0-9a-fA-F]+)\\t([0-9]+)$");
    private static final Pattern RVA = Pattern.compile("^0x[0-9a-fA-F]+$");

    private static final int MAX_VTABLES = 2;
    private static final int MAX_SLOTS = 9;
    private static final int MAX_DEPTH = 3;
    private static final int MAX_CHILDREN_PER_NODE = 8;
    private static final int MAX_NODES_PER_SLOT = 18;
    private static final int MAX_NEW_DECOMPILES = 96;

    static class VTarget {
        String name;
        String address;
        int slots;
        VTarget(String n, String a, int s) { name=n; address=a; slots=s; }
    }

    static class Node {
        Function fn;
        int depth;
        Node(Function f, int d) { fn=f; depth=d; }
    }

    private Set<String> existing = new HashSet<>();
    private Set<String> decompiledNew = new HashSet<>();
    private int newDecompileCount = 0;
    private DecompInterface decomp;
    private FunctionManager fm;
    private Memory mem;
    private int ptrSize;

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 5) {
            printerr("Usage: P1_VtableDispatchMap.java <targets.tsv> <manifest.tsv> <precheck.txt> <outDir> <mode>");
            return;
        }

        File targetsFile = new File(args[0]);
        File manifestFile = new File(args[1]);
        File precheckFile = new File(args[2]);
        File outDir = new File(args[3]);
        if (!outDir.exists() && !outDir.mkdirs()) {
            printerr("Cannot create output directory: " + outDir);
            return;
        }

        existing = readExistingManifest(manifestFile);
        List<VTarget> targets = readTargets(targetsFile);
        if (targets.size() != MAX_VTABLES) {
            printerr("Safety gate: expected exactly 2 vtables, got " + targets.size());
            return;
        }

        fm = currentProgram.getFunctionManager();
        mem = currentProgram.getMemory();
        ptrSize = currentProgram.getCompilerSpec().getDataOrganization().getPointerSize();
        if (ptrSize != 8) {
            printerr("Safety gate: expected 64-bit pointer size, got " + ptrSize);
            return;
        }

        decomp = new DecompInterface();
        decomp.toggleCCode(true);
        decomp.toggleSyntaxTree(true);
        decomp.setSimplificationStyle("decompile");
        if (!decomp.openProgram(currentProgram)) {
            printerr("Decompiler failed to open program");
            return;
        }

        File newDir = new File(outDir, "NEW_DECOMPILE");
        if (!newDir.exists()) newDir.mkdirs();

        try (
            PrintWriter slotOut = writer(new File(outDir, "P1_SLOT_RAW.tsv"));
            PrintWriter edgeOut = writer(new File(outDir, "P1_CALL_CHAIN_RAW.tsv"));
            PrintWriter runOut = writer(new File(outDir, "P1_GHIDRA_RUN.txt"))
        ) {
            slotOut.println("class\tvtable\tslot\tslot_address\ttarget\tfunction_name\thas_existing_decompile\tinstruction_count\tcaller_count\tdirect_callee_count");
            edgeOut.println("class\tvtable\tslot\tdepth\tfrom_rva\tto_rva\tfrom_name\tto_name\tto_has_existing_decompile\tto_instruction_count\tto_direct_callee_count");

            runOut.println("CSMC P1 VTABLE DISPATCH MAP");
            runOut.println("semantic_promotion=false");
            runOut.println("scope=2_vtables_18_slots_plus_one_precheck");
            runOut.println("max_depth=" + MAX_DEPTH);
            runOut.println("existing_manifest_entries=" + existing.size());

            runPrecheck(precheckFile, outDir, runOut);

            for (VTarget vt : targets) {
                Address base = parseAddress(vt.address);
                runOut.println();
                runOut.println("VTABLE " + vt.name + " " + base + " slots=" + vt.slots);
                for (int slot = 0; slot < vt.slots; slot++) {
                    Address slotAddr = base.add((long)slot * ptrSize);
                    Address targetAddr = readPointer(slotAddr);
                    if (targetAddr == null) {
                        slotOut.println(vt.name+"\t"+base+"\t"+slot+"\t"+slotAddr+"\tREAD_FAILED\t\t0\t0\t0\t0");
                        continue;
                    }
                    Function root = resolveFunction(targetAddr);
                    if (root == null) {
                        slotOut.println(vt.name+"\t"+base+"\t"+slot+"\t"+slotAddr+"\t"+targetAddr+"\tNO_FUNCTION\t0\t0\t0\t0");
                        continue;
                    }

                    String rootRva = norm(root.getEntryPoint());
                    int insn = instructionCount(root);
                    Set<Function> callers = getCallers(root, 200);
                    List<Function> callees = getCallees(root, MAX_CHILDREN_PER_NODE);
                    boolean hasExisting = existing.contains(rootRva);

                    slotOut.println(vt.name+"\t"+base+"\t"+slot+"\t"+slotAddr+"\t"+rootRva+"\t"+root.getName()+"\t"+bool(hasExisting)+"\t"+insn+"\t"+callers.size()+"\t"+callees.size());

                    if (!hasExisting) decompileNew(root, newDir);
                    exploreBounded(vt, slot, root, edgeOut, newDir);
                }
            }

            runOut.println();
            runOut.println("new_decompile_count=" + newDecompileCount);
        } finally {
            decomp.dispose();
        }

        println("P1 raw outputs written to: " + outDir.getAbsolutePath());
    }

    private void runPrecheck(File precheckFile, File outDir, PrintWriter runOut) throws Exception {
        if (!precheckFile.isFile()) return;
        String addrText = "";
        try (BufferedReader br = new BufferedReader(new InputStreamReader(new FileInputStream(precheckFile), StandardCharsets.UTF_8))) {
            String line;
            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.length() == 0 || line.startsWith("#")) continue;
                if (RVA.matcher(line).matches()) { addrText = line; break; }
            }
        }
        if (addrText.length() == 0) return;

        Address a = parseAddress(addrText);
        Function fn = resolveFunction(a);
        File report = new File(outDir, "P1_PRECHECK_1400452b0.txt");
        try (PrintWriter pw = writer(report)) {
            pw.println("rva=" + addrText.toLowerCase());
            if (fn == null) {
                pw.println("status=NO_FUNCTION");
                return;
            }
            String rva = norm(fn.getEntryPoint());
            boolean hasExisting = existing.contains(rva);
            pw.println("function=" + fn.getName());
            pw.println("entry=" + rva);
            pw.println("has_existing_decompile=" + bool(hasExisting));
            pw.println("instruction_count=" + instructionCount(fn));
            pw.println("direct_callees=" + getCallees(fn, MAX_CHILDREN_PER_NODE).size());

            if (hasExisting) {
                pw.println("decompile=SKIPPED_EXISTING");
            } else {
                String c = decompileFunction(fn);
                pw.println("decompile_begin");
                pw.println(c);
                pw.println("decompile_end");
                decompileNew(fn, new File(outDir, "NEW_DECOMPILE"));
            }
        }
        runOut.println("precheck=" + addrText.toLowerCase());
    }

    private void exploreBounded(VTarget vt, int slot, Function root, PrintWriter edgeOut, File newDir) {
        ArrayDeque<Node> q = new ArrayDeque<>();
        Set<String> seen = new LinkedHashSet<>();
        q.add(new Node(root, 0));
        seen.add(norm(root.getEntryPoint()));

        while (!q.isEmpty() && seen.size() < MAX_NODES_PER_SLOT) {
            Node n = q.removeFirst();
            if (n.depth >= MAX_DEPTH) continue;

            int nInsn = instructionCount(n.fn);
            // Root is always expanded. Deeper expansion is wrapper-biased.
            if (n.depth > 0 && nInsn > 120) continue;

            List<Function> children = getCallees(n.fn, MAX_CHILDREN_PER_NODE);
            for (Function child : children) {
                if (seen.size() >= MAX_NODES_PER_SLOT) break;
                String childRva = norm(child.getEntryPoint());
                int childDepth = n.depth + 1;
                boolean childExisting = existing.contains(childRva);
                int childInsn = instructionCount(child);
                int childCallees = getCallees(child, MAX_CHILDREN_PER_NODE).size();

                edgeOut.println(
                    vt.name+"\t"+vt.address+"\t"+slot+"\t"+childDepth+"\t"+
                    norm(n.fn.getEntryPoint())+"\t"+childRva+"\t"+
                    n.fn.getName()+"\t"+child.getName()+"\t"+bool(childExisting)+"\t"+
                    childInsn+"\t"+childCallees
                );

                if (!childExisting) decompileNew(child, newDir);
                if (seen.add(childRva)) {
                    q.addLast(new Node(child, childDepth));
                }
            }
        }
    }

    private void decompileNew(Function fn, File newDir) {
        if (newDecompileCount >= MAX_NEW_DECOMPILES) return;
        String rva = norm(fn.getEntryPoint());
        if (existing.contains(rva) || decompiledNew.contains(rva)) return;
        decompiledNew.add(rva);
        String c = decompileFunction(fn);
        File f = new File(newDir, fn.getName() + "_" + rva.substring(2) + ".c.txt");
        try (PrintWriter pw = writer(f)) {
            pw.println("// P1 NEW_ONLY");
            pw.println("// rva=" + rva);
            pw.println(c);
        } catch (Exception e) {
            printerr("Failed writing decompile for " + rva + ": " + e);
        }
        newDecompileCount++;
    }

    private String decompileFunction(Function fn) {
        try {
            DecompileResults r = decomp.decompileFunction(fn, 60, monitor);
            if (r != null && r.decompileCompleted() && r.getDecompiledFunction() != null) {
                return r.getDecompiledFunction().getC();
            }
        } catch (Exception e) {
            return "DECOMPILE_EXCEPTION: " + e;
        }
        return "DECOMPILE_FAILED";
    }

    private Set<String> readExistingManifest(File f) throws Exception {
        Set<String> out = new HashSet<>();
        if (!f.isFile()) return out;
        try (BufferedReader br = new BufferedReader(new InputStreamReader(new FileInputStream(f), StandardCharsets.UTF_8))) {
            String line;
            boolean first = true;
            while ((line = br.readLine()) != null) {
                if (first) { first = false; continue; }
                String[] p = line.split("\\t", -1);
                if (p.length > 0 && RVA.matcher(p[0].trim()).matches()) out.add(p[0].trim().toLowerCase());
            }
        }
        return out;
    }

    private List<VTarget> readTargets(File f) throws Exception {
        List<VTarget> out = new ArrayList<>();
        try (BufferedReader br = new BufferedReader(new InputStreamReader(new FileInputStream(f), StandardCharsets.UTF_8))) {
            String line;
            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.length() == 0 || line.startsWith("#")) continue;
                Matcher m = TARGET_LINE.matcher(line);
                if (!m.matches()) continue;
                int slots = Integer.parseInt(m.group(3));
                if (slots != MAX_SLOTS) continue;
                out.add(new VTarget(m.group(1), m.group(2), slots));
            }
        }
        return out;
    }

    private Address readPointer(Address a) {
        try {
            long raw = mem.getLong(a);
            return toAddr(raw);
        } catch (Exception e) {
            return null;
        }
    }

    private Address parseAddress(String s) {
        String h = s.toLowerCase().startsWith("0x") ? s.substring(2) : s;
        return toAddr(Long.parseUnsignedLong(h, 16));
    }

    private Function resolveFunction(Address a) {
        Function f = fm.getFunctionAt(a);
        if (f == null) f = fm.getFunctionContaining(a);
        return f;
    }

    private int instructionCount(Function fn) {
        int n = 0;
        InstructionIterator it = currentProgram.getListing().getInstructions(fn.getBody(), true);
        while (it.hasNext() && n < 100000) { it.next(); n++; }
        return n;
    }

    private Set<Function> getCallers(Function fn, int cap) {
        Set<Function> result = new LinkedHashSet<>();
        ReferenceIterator refs = currentProgram.getReferenceManager().getReferencesTo(fn.getEntryPoint());
        while (refs.hasNext() && result.size() < cap) {
            Reference ref = refs.next();
            if (!ref.getReferenceType().isCall()) continue;
            Function caller = fm.getFunctionContaining(ref.getFromAddress());
            if (caller != null) result.add(caller);
        }
        return result;
    }

    private List<Function> getCallees(Function fn, int cap) {
        LinkedHashMap<String, Function> map = new LinkedHashMap<>();
        AddressSetView body = fn.getBody();
        InstructionIterator it = currentProgram.getListing().getInstructions(body, true);
        while (it.hasNext() && map.size() < cap) {
            Instruction ins = it.next();
            for (Reference ref : ins.getReferencesFrom()) {
                if (!ref.getReferenceType().isCall()) continue;
                Function callee = fm.getFunctionAt(ref.getToAddress());
                if (callee == null) callee = fm.getFunctionContaining(ref.getToAddress());
                if (callee != null) map.put(norm(callee.getEntryPoint()), callee);
                if (map.size() >= cap) break;
            }
        }
        return new ArrayList<>(map.values());
    }

    private String norm(Address a) {
        return "0x" + a.toString().toLowerCase();
    }

    private int bool(boolean b) { return b ? 1 : 0; }

    private PrintWriter writer(File f) throws Exception {
        return new PrintWriter(new BufferedWriter(new OutputStreamWriter(new FileOutputStream(f), StandardCharsets.UTF_8)));
    }
}
