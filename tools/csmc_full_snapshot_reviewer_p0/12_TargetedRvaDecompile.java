// TargetedRvaDecompile.java
// P0 targeted-only Ghidra postScript.
// Decompiles only RVAs/addresses explicitly listed in ghidra_targets.txt.

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSetView;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStreamReader;
import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class TargetedRvaDecompile extends GhidraScript {

    private static final Pattern HEX = Pattern.compile("0x([0-9a-fA-F]+)");
    private static final int MAX_TARGETS = 12;
    private static final int MAX_CALL_EDGES = 60;

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 2) {
            printerr("Usage: TargetedRvaDecompile.java <targetsFile> <outDir>");
            return;
        }

        File targetsFile = new File(args[0]);
        File outDir = new File(args[1]);

        if (!targetsFile.isFile()) {
            printerr("Targets file not found: " + targetsFile);
            return;
        }
        if (!outDir.exists() && !outDir.mkdirs()) {
            printerr("Cannot create output dir: " + outDir);
            return;
        }

        List<String> targets = readTargets(targetsFile);
        if (targets.size() == 0) {
            println("No targets. Nothing to do.");
            return;
        }
        if (targets.size() > MAX_TARGETS) {
            printerr("Refusing broad pass: target count > " + MAX_TARGETS);
            return;
        }

        DecompInterface decomp = new DecompInterface();
        decomp.toggleCCode(true);
        decomp.toggleSyntaxTree(true);
        decomp.setSimplificationStyle("decompile");

        if (!decomp.openProgram(currentProgram)) {
            printerr("Decompiler failed to open program.");
            return;
        }

        File summaryFile = new File(outDir, "GHIDRA_TARGETED_SUMMARY.txt");
        try (PrintWriter summary = writer(summaryFile)) {
            summary.println("CSMC FULL SNAPSHOT REVIEWER P0 — GHIDRA TARGETED PASS");
            summary.println("====================================================");
            summary.println();
            summary.println("program=" + currentProgram.getName());
            summary.println("image_base=" + currentProgram.getImageBase());
            summary.println("target_count=" + targets.size());
            summary.println("broad_scan=false");
            summary.println();

            int index = 0;
            for (String token : targets) {
                monitor.checkCancelled();
                index++;

                Address requested = resolveTarget(token);
                if (requested == null) {
                    summary.println(index + "\t" + token + "\tUNRESOLVED");
                    continue;
                }

                Function fn = currentProgram.getFunctionManager().getFunctionContaining(requested);
                if (fn == null) {
                    fn = currentProgram.getFunctionManager().getFunctionAt(requested);
                }

                String safe = token.replace("0x", "").replaceAll("[^0-9A-Fa-f]", "_");
                File outFile = new File(
                    outDir,
                    String.format("target_%02d_%s.txt", index, safe)
                );

                if (fn == null) {
                    try (PrintWriter out = writer(outFile)) {
                        out.println("requested=" + token);
                        out.println("resolved_address=" + requested);
                        out.println("function=NOT_FOUND");
                    }
                    summary.println(index + "\t" + token + "\t" + requested + "\tFUNCTION_NOT_FOUND");
                    continue;
                }

                DecompileResults results = decomp.decompileFunction(fn, 120, monitor);
                String ccode = "";
                if (results != null && results.decompileCompleted() &&
                    results.getDecompiledFunction() != null) {
                    ccode = results.getDecompiledFunction().getC();
                }

                Set<Function> callers = getCallers(fn);
                Set<Function> callees = getCallees(fn);

                try (PrintWriter out = writer(outFile)) {
                    out.println("CSMC P0 TARGETED DECOMPILE");
                    out.println("==========================");
                    out.println();
                    out.println("requested=" + token);
                    out.println("resolved_address=" + requested);
                    out.println("function_name=" + fn.getName());
                    out.println("function_entry=" + fn.getEntryPoint());
                    out.println("function_body_min=" + fn.getBody().getMinAddress());
                    out.println("function_body_max=" + fn.getBody().getMaxAddress());
                    out.println();
                    out.println("[CALLERS]");
                    writeFunctions(out, callers);
                    out.println();
                    out.println("[CALLEES]");
                    writeFunctions(out, callees);
                    out.println();
                    out.println("[DECOMPILE]");
                    if (ccode.isEmpty()) {
                        out.println("DECOMPILE_FAILED");
                        if (results != null) {
                            out.println("error=" + results.getErrorMessage());
                        }
                    } else {
                        out.println(ccode);
                    }
                }

                summary.println(
                    index + "\t" + token + "\t" +
                    requested + "\t" + fn.getEntryPoint() + "\t" +
                    fn.getName() + "\tcallers=" + callers.size() +
                    "\tcallees=" + callees.size()
                );
            }

            summary.println();
            summary.println("semantic_promotion=false");
            summary.println("scope=targeted_rva_only");
        } finally {
            decomp.dispose();
        }

        println("Targeted Ghidra output: " + outDir.getAbsolutePath());
    }

    private List<String> readTargets(File f) throws Exception {
        List<String> result = new ArrayList<>();

        try (BufferedReader br = new BufferedReader(
                new InputStreamReader(
                    new FileInputStream(f),
                    StandardCharsets.UTF_8))) {

            String line;
            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.length() == 0 || line.startsWith("#")) {
                    continue;
                }

                Matcher m = HEX.matcher(line);
                if (m.find()) {
                    String token = "0x" + m.group(1);
                    if (!result.contains(token)) {
                        result.add(token);
                    }
                }
            }
        }

        return result;
    }

    private Address resolveTarget(String token) {
        try {
            String hex = token.toLowerCase().startsWith("0x")
                ? token.substring(2)
                : token;

            long value = Long.parseUnsignedLong(hex, 16);
            long imageBase = currentProgram.getImageBase().getOffset();

            if (Long.compareUnsigned(value, imageBase) >= 0) {
                return toAddr(value);
            }

            return currentProgram.getImageBase().add(value);
        } catch (Exception e) {
            printerr("resolveTarget failed for " + token + ": " + e);
            return null;
        }
    }

    private Set<Function> getCallers(Function fn) {
        Set<Function> result = new LinkedHashSet<>();
        FunctionManager fm = currentProgram.getFunctionManager();
        ReferenceIterator refs =
            currentProgram.getReferenceManager().getReferencesTo(fn.getEntryPoint());

        while (refs.hasNext() && result.size() < MAX_CALL_EDGES) {
            Reference ref = refs.next();
            if (!ref.getReferenceType().isCall()) {
                continue;
            }
            Function caller = fm.getFunctionContaining(ref.getFromAddress());
            if (caller != null) {
                result.add(caller);
            }
        }

        return result;
    }

    private Set<Function> getCallees(Function fn) {
        Set<Function> result = new LinkedHashSet<>();
        FunctionManager fm = currentProgram.getFunctionManager();
        AddressSetView body = fn.getBody();
        InstructionIterator it =
            currentProgram.getListing().getInstructions(body, true);

        while (it.hasNext() && result.size() < MAX_CALL_EDGES) {
            Instruction ins = it.next();
            Reference[] refs = ins.getReferencesFrom();

            for (Reference ref : refs) {
                if (!ref.getReferenceType().isCall()) {
                    continue;
                }
                Function callee = fm.getFunctionAt(ref.getToAddress());
                if (callee == null) {
                    callee = fm.getFunctionContaining(ref.getToAddress());
                }
                if (callee != null) {
                    result.add(callee);
                }
                if (result.size() >= MAX_CALL_EDGES) {
                    break;
                }
            }
        }

        return result;
    }

    private void writeFunctions(PrintWriter out, Set<Function> funcs) {
        if (funcs.isEmpty()) {
            out.println("NONE");
            return;
        }

        for (Function f : funcs) {
            out.println(f.getEntryPoint() + "\t" + f.getName());
        }
    }

    private PrintWriter writer(File file) throws Exception {
        return new PrintWriter(
            new BufferedWriter(
                new OutputStreamWriter(
                    new FileOutputStream(file),
                    StandardCharsets.UTF_8)));
    }
}
