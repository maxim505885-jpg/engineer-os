"""Linux DOC conversion child: limits and network denial before exec."""
import ctypes
import ctypes.util
import errno
import os
import resource
import sys


def apply():
    if sys.platform!='linux':raise RuntimeError('DOC sandbox is Linux only')
    library=ctypes.util.find_library('seccomp')
    if not library:raise RuntimeError('Network sandbox unavailable')
    lib=ctypes.CDLL(library)
    lib.seccomp_init.argtypes=[ctypes.c_uint32];lib.seccomp_init.restype=ctypes.c_void_p
    lib.seccomp_syscall_resolve_name.argtypes=[ctypes.c_char_p];lib.seccomp_syscall_resolve_name.restype=ctypes.c_int
    lib.seccomp_rule_add.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_int,ctypes.c_uint];lib.seccomp_rule_add.restype=ctypes.c_int
    lib.seccomp_load.argtypes=[ctypes.c_void_p];lib.seccomp_load.restype=ctypes.c_int
    lib.seccomp_release.argtypes=[ctypes.c_void_p]
    context=lib.seccomp_init(0x7fff0000)
    if not context:raise RuntimeError('Sandbox creation failed')
    try:
        for name in ['socket','connect','sendto','sendmsg','sendmmsg','socketcall','io_uring_setup']:
            call=lib.seccomp_syscall_resolve_name(name.encode())
            if call>=0 and lib.seccomp_rule_add(context,0x00050000|errno.EPERM,call,0)!=0:raise RuntimeError('Network rule failed')
        if lib.seccomp_load(context)!=0:raise RuntimeError('Network denial failed')
    finally:lib.seccomp_release(context)
    resource.setrlimit(resource.RLIMIT_CPU,(90,90))
    resource.setrlimit(resource.RLIMIT_AS,(3*1024**3,3*1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE,(100*1024**2,100*1024**2))
    resource.setrlimit(resource.RLIMIT_NOFILE,(512,512))


if __name__=='__main__':
    apply()
    args=sys.argv[1:]
    if not args or not os.path.isabs(args[0]):raise SystemExit(2)
    os.execv(args[0],args)
