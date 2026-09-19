// VtableDispatchProbe.java
// P0.8 exact-address vtable / indirect-dispatch probe.
// Reads only the explicitly listed vtables and their fixed slot counts.

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

public class VtableDispatchProbe extends GhidraScript {
    private static final Pattern LINE = Pattern.compile("^([^\\t]+)\\t(0x[0-9a-fA-F]+)\\t([0-9]+)$");
    private static final int MAX_VTABLES = 4;
    private static final int MAX_SLOTS = 16;
    private static final int MAX_CALL_EDGES = 60;

    static class VTarget {
        String name; String address; int slots;
        VTarget(String n, String a, int s) { name=n; address=a; slots=s; }
    }

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 2) { printerr("Usage: VtableDispatchProbe.java <targetsFile> <outDir>"); return; }
        File targetsFile = new File(args[0]);
        File outDir = new File(args[1]);
        if (!targetsFile.isFile()) { printerr("Targets file missing: "+targetsFile); return; }
        if (!outDir.exists() && !outDir.mkdirs()) { printerr("Cannot create output dir: "+outDir); return; }

        List<VTarget> targets = readTargets(targetsFile);
        if (targets.size() == 0 || targets.size() > MAX_VTABLES) { printerr("Invalid vtable target count: "+targets.size()); return; }

        DecompInterface decomp = new DecompInterface();
        decomp.toggleCCode(true);
        decomp.toggleSyntaxTree(true);
        decomp.setSimplificationStyle("decompile");
        if (!decomp.openProgram(currentProgram)) { printerr("Decompiler failed to open program"); return; }

        File tsv = new File(outDir, "VTABLE_DISPATCH_SUMMARY.tsv");
        File report = new File(outDir, "VTABLE_DISPATCH_REPORT.txt");
        Memory mem = currentProgram.getMemory();
        FunctionManager fm = currentProgram.getFunctionManager();
        int ptrSize = currentProgram.getCompilerSpec().getDataOrganization().getPointerSize();

        try (PrintWriter sw = writer(tsv); PrintWriter rw = writer(report)) {
            sw.println("vtable\tvtable_address\tslot\tslot_address\tfunction_pointer\tfunction_name\tfunction_entry\trefs_to_slot\tcallers\tcallees\tkeyword_hits");
            rw.println("CSMC P0.8 VTABLE / INDIRECT DISPATCH REPORT");
            rw.println("semantic_promotion=false");
            rw.println("scope=two_known_loader_vtables_only");
            rw.println("pointer_size="+ptrSize);

            for (VTarget vt : targets) {
                Address base = parseAddress(vt.address);
                rw.println(); rw.println("============================================================");
                rw.println("VTABLE "+vt.name+" @ "+base+" slots="+vt.slots);
                rw.println("============================================================");
                rw.println("refs_to_vtable_base="+countRefs(base));

                for (int i=0; i<vt.slots; i++) {
                    Address slotAddr = base.add((long)i * ptrSize);
                    long raw;
                    try { raw = mem.getLong(slotAddr); }
                    catch (Exception e) {
                        sw.println(vt.name+"\t"+base+"\t"+i+"\t"+slotAddr+"\tREAD_FAILED\t\t\t"+countRefs(slotAddr)+"\t0\t0\t");
                        rw.println("slot["+i+"] "+slotAddr+" READ_FAILED "+e);
                        continue;
                    }
                    Address fnAddr = toAddr(raw);
                    Function fn = fm.getFunctionAt(fnAddr);
                    if (fn == null) fn = fm.getFunctionContaining(fnAddr);
                    int refs = countRefs(slotAddr);
                    if (fn == null) {
                        sw.println(vt.name+"\t"+base+"\t"+i+"\t"+slotAddr+"\t"+fnAddr+"\tNO_FUNCTION\t\t"+refs+"\t0\t0\t");
                        rw.println("slot["+i+"] "+slotAddr+" -> "+fnAddr+" NO_FUNCTION refs_to_slot="+refs);
                        continue;
                    }

                    Set<Function> callers = getCallers(fn);
                    Set<Function> callees = getCallees(fn);
                    String ccode = decompile(decomp, fn);
                    String hits = keywordHits(ccode);
                    sw.println(vt.name+"\t"+base+"\t"+i+"\t"+slotAddr+"\t"+fnAddr+"\t"+fn.getName()+"\t"+fn.getEntryPoint()+"\t"+refs+"\t"+callers.size()+"\t"+callees.size()+"\t"+hits);

                    rw.println();
                    rw.println("slot["+i+"] "+slotAddr+" -> "+fnAddr+" "+fn.getName());
                    rw.println("entry="+fn.getEntryPoint()+" refs_to_slot="+refs+" callers="+callers.size()+" callees="+callees.size());
                    rw.println("keyword_hits="+hits);
                    rw.println("[CALLERS]"); writeFunctions(rw, callers);
                    rw.println("[CALLEES]"); writeFunctions(rw, callees);
                    rw.println("[DECOMPILE]"); rw.println(ccode.length()==0 ? "DECOMPILE_FAILED" : ccode);
                }
            }
        } finally { decomp.dispose(); }
        println("Vtable dispatch output: "+outDir.getAbsolutePath());
    }

    private List<VTarget> readTargets(File f) throws Exception {
        List<VTarget> out = new ArrayList<>();
        try (BufferedReader br = new BufferedReader(new InputStreamReader(new FileInputStream(f), StandardCharsets.UTF_8))) {
            String line;
            while ((line=br.readLine())!=null) {
                line=line.trim();
                if (line.length()==0 || line.startsWith("#")) continue;
                Matcher m=LINE.matcher(line);
                if (!m.matches()) continue;
                int slots=Integer.parseInt(m.group(3));
                if (slots<1 || slots>MAX_SLOTS) continue;
                out.add(new VTarget(m.group(1),m.group(2),slots));
            }
        }
        return out;
    }

    private Address parseAddress(String s) {
        String h=s.toLowerCase().startsWith("0x") ? s.substring(2) : s;
        return toAddr(Long.parseUnsignedLong(h,16));
    }

    private int countRefs(Address a) {
        int n=0; ReferenceIterator it=currentProgram.getReferenceManager().getReferencesTo(a);
        while (it.hasNext() && n<10000) { it.next(); n++; }
        return n;
    }

    private String decompile(DecompInterface d, Function fn) {
        try {
            DecompileResults r=d.decompileFunction(fn,60,monitor);
            if (r!=null && r.decompileCompleted() && r.getDecompiledFunction()!=null) return r.getDecompiledFunction().getC();
        } catch (Exception e) { return "DECOMPILE_EXCEPTION: "+e; }
        return "";
    }

    private String keywordHits(String c) {
        String low=c.toLowerCase();
        String[] terms={"read","stream","buffer","memcpy","modeldata","canvas3dmodelloader","factory","vtable","virtual","bone","weight","skin","matrix","transform","glbuffersubdata","glbufferdata"};
        List<String> hits=new ArrayList<>();
        for (String t:terms) if (low.contains(t)) hits.add(t);
        return String.join(",",hits);
    }

    private Set<Function> getCallers(Function fn) {
        Set<Function> result=new LinkedHashSet<>();
        FunctionManager fm=currentProgram.getFunctionManager();
        ReferenceIterator refs=currentProgram.getReferenceManager().getReferencesTo(fn.getEntryPoint());
        while (refs.hasNext() && result.size()<MAX_CALL_EDGES) {
            Reference ref=refs.next();
            if (!ref.getReferenceType().isCall()) continue;
            Function caller=fm.getFunctionContaining(ref.getFromAddress());
            if (caller!=null) result.add(caller);
        }
        return result;
    }

    private Set<Function> getCallees(Function fn) {
        Set<Function> result=new LinkedHashSet<>();
        FunctionManager fm=currentProgram.getFunctionManager();
        AddressSetView body=fn.getBody();
        InstructionIterator it=currentProgram.getListing().getInstructions(body,true);
        while (it.hasNext() && result.size()<MAX_CALL_EDGES) {
            Instruction ins=it.next();
            for (Reference ref:ins.getReferencesFrom()) {
                if (!ref.getReferenceType().isCall()) continue;
                Function callee=fm.getFunctionAt(ref.getToAddress());
                if (callee==null) callee=fm.getFunctionContaining(ref.getToAddress());
                if (callee!=null) result.add(callee);
                if (result.size()>=MAX_CALL_EDGES) break;
            }
        }
        return result;
    }

    private void writeFunctions(PrintWriter out, Set<Function> funcs) {
        if (funcs.isEmpty()) { out.println("NONE"); return; }
        for (Function f:funcs) out.println(f.getEntryPoint()+"\t"+f.getName());
    }

    private PrintWriter writer(File file) throws Exception {
        return new PrintWriter(new BufferedWriter(new OutputStreamWriter(new FileOutputStream(file),StandardCharsets.UTF_8)));
    }
}
