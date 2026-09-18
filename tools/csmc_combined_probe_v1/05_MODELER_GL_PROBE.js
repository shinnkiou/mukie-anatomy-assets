"use strict";

const BODY_SIZE = 1160128;
const EBO_SIZE = 751056;
const GL_ARRAY_BUFFER = 0x8892;
const GL_ELEMENT_ARRAY_BUFFER = 0x8893;

const bindings = {};
const hooked = {};

function tid() {
    return Process.getCurrentThreadId();
}

function state() {
    const k = tid().toString();
    if (!(k in bindings)) bindings[k] = { array: 0, element: 0 };
    return bindings[k];
}

function backtrace(ctx) {
    try {
        return Thread.backtrace(ctx, Backtracer.ACCURATE)
            .slice(0, 24)
            .map(function(x) { return DebugSymbol.fromAddress(x).toString(); });
    } catch (e) {
        return [];
    }
}

function sendUpload(api, ctx, target, offset, size, data) {
    if (size !== BODY_SIZE && size !== EBO_SIZE) return;

    const s = state();
    let bound = 0;
    if (target === GL_ARRAY_BUFFER) bound = s.array;
    if (target === GL_ELEMENT_ARRAY_BUFFER) bound = s.element;

    const payload = {
        type: "upload",
        api: api,
        thread: tid(),
        target: target,
        bound: bound,
        offset: offset,
        size: size,
        data: data.toString(),
        backtrace: backtrace(ctx)
    };

    if (data.isNull()) {
        send(payload);
        return;
    }

    try {
        send(payload, data.readByteArray(size));
    } catch (e) {
        payload.read_error = e.toString();
        send(payload);
    }
}

function hook(name, address) {
    if (address === null || address.isNull()) return;
    const key = address.toString();
    if (hooked[key]) return;
    hooked[key] = name;

    if (name === "glBindBuffer" || name === "glBindBufferARB") {
        Interceptor.attach(address, {
            onEnter: function(args) {
                const target = args[0].toUInt32();
                const buffer = args[1].toUInt32();
                const s = state();
                if (target === GL_ARRAY_BUFFER) s.array = buffer;
                if (target === GL_ELEMENT_ARRAY_BUFFER) s.element = buffer;
            }
        });
        return;
    }

    if (name === "glBufferData" || name === "glBufferDataARB") {
        Interceptor.attach(address, {
            onEnter: function(args) {
                sendUpload(name, this.context, args[0].toUInt32(), 0, args[1].toInt32(), args[2]);
            }
        });
        return;
    }

    if (name === "glBufferSubData" || name === "glBufferSubDataARB") {
        Interceptor.attach(address, {
            onEnter: function(args) {
                sendUpload(name, this.context, args[0].toUInt32(), args[1].toInt32(), args[2].toInt32(), args[3]);
            }
        });
    }
}

const interesting = {
    "glBindBuffer": true,
    "glBindBufferARB": true,
    "glBufferData": true,
    "glBufferDataARB": true,
    "glBufferSubData": true,
    "glBufferSubDataARB": true
};

function installResolverHook(address, procNameArgIndex) {
    Interceptor.attach(address, {
        onEnter: function(args) {
            this.name = null;
            try { this.name = args[procNameArgIndex].readCString(); } catch (e) {}
        },
        onLeave: function(retval) {
            if (!this.name) return;
            if (!(this.name in interesting)) return;
            if (retval.isNull()) return;
            hook(this.name, retval);
        }
    });
}

const ogl = Process.getModuleByName("opengl32.dll");
installResolverHook(ogl.getExportByName("wglGetProcAddress"), 0);

const kernel = Process.getModuleByName("kernel32.dll");
installResolverHook(kernel.getExportByName("GetProcAddress"), 1);

send({ type: "status", message: "resolver hooks installed" });
