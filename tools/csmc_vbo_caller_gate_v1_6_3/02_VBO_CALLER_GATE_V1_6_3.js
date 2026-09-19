"use strict";

const BODY_SIZE = 1160128;
const GL_ARRAY_BUFFER = 0x8892;
const GL_ELEMENT_ARRAY_BUFFER = 0x8893;
const MAX_CACHE = 96;
const MAX_BACKTRACE = 24;

const bindings = {};
const hooked = {};
const candidates = [];
let seq = 0;

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

function frameInfo(address, index) {
    let moduleName = "";
    let moduleBase = "";
    let rva = "";
    let symbol = "";

    try {
        const m = Process.findModuleByAddress(address);
        if (m !== null) {
            moduleName = m.name || "";
            moduleBase = m.base.toString();
            rva = "0x" + address.sub(m.base).toString(16);
        }
    } catch (e) {}

    try {
        symbol = DebugSymbol.fromAddress(address).toString();
    } catch (e) {}

    return {
        frame_index: index,
        address: address.toString(),
        module: moduleName,
        module_base: moduleBase,
        rva: rva,
        symbol: symbol
    };
}

function captureFrames(ctx) {
    const frames = [];
    try {
        const bt = Thread.backtrace(ctx, Backtracer.ACCURATE);
        const count = Math.min(bt.length, MAX_BACKTRACE);
        for (let i = 0; i < count; i++) {
            frames.push(frameInfo(bt[i], i));
        }
    } catch (e) {
        emit({
            kind: "status",
            message: "backtrace capture failed",
            error: String(e)
        });
    }
    return frames;
}

function cacheCandidate(data, apiName, ctx, target, bound, offset, size) {
    if (!data || data.isNull()) return;

    try {
        const copy = data.readByteArray(BODY_SIZE);
        const frames = captureFrames(ctx);

        const rec = {
            upload_seq: ++seq,
            captured_ms: Date.now(),
            thread: tid(),
            api: apiName,
            target: target,
            bound: bound,
            offset: offset,
            size: size,
            data_ptr: data.toString(),
            frames: frames,
            bytes: copy
        };

        candidates.push(rec);
        while (candidates.length > MAX_CACHE) {
            candidates.shift();
        }

        send({
            kind: "body_upload",
            seq: rec.upload_seq,
            upload_seq: rec.upload_seq,
            captured_ms: rec.captured_ms,
            thread: rec.thread,
            api: rec.api,
            target: rec.target,
            bound: rec.bound,
            offset: rec.offset,
            size: rec.size,
            data_ptr: rec.data_ptr,
            frames: rec.frames,
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
    if (address === null || address.isNull()) return;

    const key = address.toString();
    if (hooked[key]) return;
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
                captured_ms: c.captured_ms,
                thread: c.thread,
                api: c.api,
                target: c.target,
                bound: c.bound,
                offset: c.offset,
                size: c.size,
                data_ptr: c.data_ptr,
                frames: c.frames
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

function clearCandidates() {
    candidates.splice(0, candidates.length);
    emit({
        kind: "status",
        message: "candidate cache cleared"
    });
}

function commandLoop() {
    recv("command", function(message) {
        const p = message.payload || {};

        try {
            if (p.cmd === "dump_candidates") {
                dumpCandidates(String(p.tag || "batch"));
            } else if (p.cmd === "clear_candidates") {
                clearCandidates();
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
