from .translate import LLVM_OUT_FILE

NEWLINE = "\n"
TAB = "\t"


def llvm_preamble():
    LLVM_OUT_FILE.writelines([
        f"; ModuleID = '{LLVM_OUT_FILE.name}'", NEWLINE,
        f"source_filename = \"{LLVM_OUT_FILE.name}\"", NEWLINE,
        "target datalayout = \"e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128\"", NEWLINE,
        "target triple = \"x86_64-pc-linux-gnu\"", NEWLINE,
        "@print_int_fstring = private unnamed_addr constant [4 x i8] c\"%d\\0A\\00\", align 1", NEWLINE,
        "; Function Attrs: noinline nounwind optnone uwtable", NEWLINE,
        "define dso_local i32 @main() #0 {", NEWLINE
    ])


def llvm_postamble():
    LLVM_OUT_FILE.writelines([
        TAB, "ret i32 0", NEWLINE,
        "}", NEWLINE,
        "declare i32 @printf(i8*, ...) #1", NEWLINE,
        "attributes #0 = { noinline nounwind optnone uwtable \"frame-pointer\"=\"all\" \"min-legal-vector-width\"=\"0\" \"no-trapping-math\"=\"true\" \"stack-protector-buffer-size\"=\"8\" \"target-cpu\"=\"x86-64\" \"target-features\"=\"+cx8,+fxsr,+mmx,+sse,+sse2,+x87\" \"tune-cpu\"=\"generic\" }", NEWLINE,
        "attributes #1 = { \"frame-pointer\"=\"all\" \"no-trapping-math\"=\"true\" \"stack-protector-buffer-size\"=\"8\" \"target-cpu\"=\"x86-64\" \"target-features\"=\"+cx8,+fxsr,+mmx,+sse,+sse2,+x87\" \"tune-cpu\"=\"generic\" }", NEWLINE,
        "!llvm.module.flags = !{!0, !1, !2, !3, !4}", NEWLINE,
        "!llvm.ident = !{!5}", NEWLINE,
        "!0 = !{i32 1, !\"wchar_size\", i32 4}", NEWLINE,
        "!1 = !{i32 7, !\"PIC Level\", i32 2}", NEWLINE,
        "!2 = !{i32 7, !\"PIE Level\", i32 2}", NEWLINE,
        "!3 = !{i32 7, !\"uwtable\", i32 1}", NEWLINE,
        "!4 = !{i32 7, !\"frame-pointer\", i32 2}", NEWLINE,
        "!5 = !{!\"Ubuntu clang version 10.0.0-4ubuntu1\"}", NEWLINE,
    ])


def llvm_stack_alloc():
    pass


def llvm_print_int(register_number: int):
    pass
