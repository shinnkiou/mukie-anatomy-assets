"use strict";

const BODY_SIZE = 1160128;
const STRIDE = 32;
const GL_ARRAY_BUFFER = 0x8892;
const GL_ELEMENT_ARRAY_BUFFER = 0x8893;
const MAX_CACHE = 16;

const bindings = {};
const hooked = {};
const candidates = [];
let seq = 0;
let monitorActive = false;
let monitorRound = 0;

function emit(obj, data) {
    obj.seq = ++seq;
    try {
        if (data !== undefined) send(obj, data);
        else send(obj);
    } catch (e) {}
}

function tid() {
    return Process.getCurrentThreadId();
}

function state() {
    const key = String(tid());
    if (!(key in bindings)) {
        bindings[key] = { array: 0, element: 0 };
    }
    return bindings[key];
}

function mainModule() {
    return Process.getModuleByName("CLIPStudioModeler.exe");
}

function rvaOf(p) {
    try {
        const m = mainModule();
        const q = ptr(p);
        if (q.compare(m.base) < 0 || q.compare(m.base.add(m.size)) >= 0) {
            return "";
        }
        return "0x" + q.sub(m.base).toString(16);
    } catch (e) {
        return "";
    }
}

function firstModelerCaller(ctx) {
    try {
        const m = mainModule();
        const bt = Thread.backtrace(ctx, Backtracer.ACCURATE);

        for (let i = 0; i < bt.length; i++) {
            const a = bt[i];
            if (a.compare(m.base) >= 0 && a.compare(m.base.add(m.size)) < 0) {
                return {
                    address: a.toString(),
                    rva: "0x" + a.sub(m.base).toString(16)
                };
            }
        }
    } catch (e) {}

    return { address: "", rva: "" };
}

function cacheCandidate(data, apiName, ctx, target, bound, offset, size) {
    if (!data || data.isNull()) {
        return;
    }

    try {
        const copy = data.readByteArray(BODY_SIZE);
        const caller = firstModelerCaller(ctx);

        const rec = {
            upload_seq: ++seq,
            api: apiName,
            thread: tid(),
            target: target,
            bound: bound,
            offset: offset,
            size: size,
            data_ptr: data.toString(),
            caller: caller.address,
            caller_rva: caller.rva,
            captured_ms: Date.now(),
            bytes: copy
        };

        candidates.push(rec);
        while (candidates.length > MAX_CACHE) {
            candidates.shift();
        }

        send({
            kind: "body_upload",
            seq: rec.upload_seq,
            api: rec.api,
            thread: rec.thread,
            target: rec.target,
            bound: rec.bound,
            offset: rec.offset,
            size: rec.size,
            data_ptr: rec.data_ptr,
            caller: rec.caller,
            caller_rva: rec.caller_rva,
            captured_ms: rec.captured_ms,
            cache_depth: candidates.length
        });

    } catch (e) {
        emit({
            kind: "status",
            message: "candidate cache copy failed",
            api: apiName,
            data_ptr: data.toString(),
            error: String(e)
        });
    }
}

function hookUpload(name, address) {
    if (address === null || address.isNull()) {
        return;
    }

    const key = address.toString();
    if (hooked[key]) {
        return;
    }

    hooked[key] = name;

    if (name === "glBindBuffer" || name === "glBindBufferARB") {
        Interceptor.attach(address, {
            onEnter(args) {
                const target = args[0].toUInt32();
                const buffer = args[1].toUInt32();
                const s = state();

                if (target === GL_ARRAY_BUFFER) {
                    s.array = buffer;
                }
                if (target === GL_ELEMENT_ARRAY_BUFFER) {
                    s.element = buffer;
                }
            }
        });
        return;
    }

    if (name === "glBufferData" || name === "glBufferDataARB") {
        Interceptor.attach(address, {
            onEnter(args) {
                const target = args[0].toUInt32();
                const size = args[1].toInt32();
                const data = args[2];

                if (
                    target !== GL_ARRAY_BUFFER ||
                    size !== BODY_SIZE ||
                    data.isNull()
                ) {
                    return;
                }

                cacheCandidate(
                    data,
                    name,
                    this.context,
                    target,
                    state().array,
                    0,
                    size
                );
            }
        });
        return;
    }

    if (name === "glBufferSubData" || name === "glBufferSubDataARB") {
        Interceptor.attach(address, {
            onEnter(args) {
                const target = args[0].toUInt32();
                const offset = args[1].toInt32();
                const size = args[2].toInt32();
                const data = args[3];

                if (
                    target !== GL_ARRAY_BUFFER ||
                    size !== BODY_SIZE ||
                    data.isNull()
                ) {
                    return;
                }

                cacheCandidate(
                    data,
                    name,
                    this.context,
                    target,
                    state().array,
                    offset,
                    size
                );
            }
        });
    }
}

const interesting = {
    glBindBuffer: true,
    glBindBufferARB: true,
    glBufferData: true,
    glBufferDataARB: true,
    glBufferSubData: true,
    glBufferSubDataARB: true
};

function installResolverHook(address, procNameArgIndex) {
    Interceptor.attach(address, {
        onEnter(args) {
            this.name = null;
            try {
                this.name = args[procNameArgIndex].readCString();
            } catch (e) {}
        },

        onLeave(retval) {
            if (
                !this.name ||
                !(this.name in interesting) ||
                retval.isNull()
            ) {
                return;
            }

            try {
                hookUpload(this.name, retval);
                emit({
                    kind: "status",
                    message: "hooked " + this.name,
                    address: retval.toString()
                });
            } catch (e) {
                emit({
                    kind: "status",
                    message: "hook failed",
                    api: this.name,
                    error: String(e)
                });
            }
        }
    });
}

function installResolvers() {
    const ogl = Process.getModuleByName("opengl32.dll");
    installResolverHook(ogl.getExportByName("wglGetProcAddress"), 0);

    const kernel = Process.getModuleByName("kernel32.dll");
    installResolverHook(kernel.getExportByName("GetProcAddress"), 1);

    emit({
        kind: "status",
        message: "OpenGL resolver hooks installed"
    });
}

function dumpCandidates(tag) {
    for (let i = 0; i < candidates.length; i++) {
        const c = candidates[i];

        try {
            send({
                kind: "candidate",
                tag: tag,
                index: i,
                upload_seq: c.upload_seq,
                api: c.api,
                thread: c.thread,
                target: c.target,
                bound: c.bound,
                offset: c.offset,
                size: c.size,
                data_ptr: c.data_ptr,
                caller: c.caller,
                caller_rva: c.caller_rva,
                captured_ms: c.captured_ms
            }, c.bytes);

        } catch (e) {
            emit({
                kind: "status",
                message: "candidate send failed",
                tag: tag,
                index: i,
                error: String(e)
            });
        }
    }

    emit({
        kind: "candidate_batch_done",
        tag: tag,
        count: candidates.length
    });
}

function stopMonitor() {
    if (!monitorActive) {
        return;
    }

    try {
        MemoryAccessMonitor.disable();
    } catch (e) {}

    monitorActive = false;

    emit({
        kind: "status",
        message: "memory monitor disabled",
        round: monitorRound
    });
}

function enableMonitor(vertices, pointers, roundNo) {
    stopMonitor();

    if (!Array.isArray(vertices) || vertices.length === 0) {
        emit({
            kind: "status",
            message: "monitor failed: no vertices",
            round: roundNo
        });
        return;
    }

    if (!Array.isArray(pointers) || pointers.length === 0) {
        emit({
            kind: "status",
            message: "monitor failed: no pointers",
            round: roundNo
        });
        return;
    }

    const ranges = [];
    const rangeMeta = [];
    const seenPages = {};

    for (let pi = 0; pi < pointers.length; pi++) {
        let basePtr;

        try {
            basePtr = ptr(pointers[pi]);
        } catch (e) {
            continue;
        }

        for (let vi = 0; vi < vertices.length; vi++) {
            const vertex = Number(vertices[vi]);
            const byteOffset = vertex * STRIDE;
            const addr = basePtr.add(byteOffset);
            const page = addr.and(ptr("0xfffffffffffff000"));
            const key = page.toString();

            if (seenPages[key]) {
                continue;
            }

            let mapped = null;
            try {
                mapped = Process.findRangeByAddress(page);
            } catch (e) {}

            if (mapped === null) {
                continue;
            }

            seenPages[key] = true;

            ranges.push({
                base: page,
                size: 4096
            });

            rangeMeta.push({
                watched_vertex: vertex,
                watched_ptr: basePtr.toString(),
                page: page.toString(),
                protection: mapped.protection
            });
        }
    }

    if (ranges.length === 0) {
        emit({
            kind: "status",
            message: "monitor failed: no mapped ranges",
            round: roundNo
        });
        return;
    }

    monitorRound = roundNo;

    try {
        MemoryAccessMonitor.enable(ranges, {
            onAccess(details) {
                let ins = "";
                let sym = "";
                let fromRva = "";

                try {
                    ins = Instruction.parse(details.from).toString();
                } catch (e) {}

                try {
                    sym = DebugSymbol.fromAddress(details.from).toString();
                } catch (e) {}

                try {
                    fromRva = rvaOf(details.from);
                } catch (e) {}

                const meta = rangeMeta[details.rangeIndex] || {};

                emit({
                    kind: "writer_access",
                    round: monitorRound,
                    operation: details.operation,
                    thread: details.threadId,
                    address: details.address.toString(),
                    from: details.from.toString(),
                    from_rva: fromRva,
                    from_symbol: sym,
                    instruction: ins,
                    range_index: details.rangeIndex,
                    page_index: details.pageIndex,
                    watched_vertex: meta.watched_vertex,
                    watched_ptr: meta.watched_ptr,
                    page_protection: meta.protection || ""
                });
            }
        });

        monitorActive = true;

        emit({
            kind: "status",
            message: "memory monitor armed",
            round: roundNo,
            range_count: ranges.length,
            vertices: vertices,
            pointer_count: pointers.length
        });

    } catch (e) {
        emit({
            kind: "status",
            message: "MemoryAccessMonitor.enable failed",
            round: roundNo,
            error: String(e)
        });
    }
}

function commandLoop() {
    recv("command", function(message) {
        const p = message.payload || {};

        try {
            if (p.cmd === "dump_candidates") {
                dumpCandidates(String(p.tag || "batch"));

            } else if (p.cmd === "monitor") {
                enableMonitor(
                    p.vertices || [],
                    p.pointers || [],
                    Number(p.round || 0)
                );

            } else if (p.cmd === "stop_monitor") {
                stopMonitor();
            }

        } catch (e) {
            emit({
                kind: "status",
                message: "command failed",
                cmd: p.cmd,
                error: String(e)
            });
        }

        commandLoop();
    });
}

installResolvers();
commandLoop();
