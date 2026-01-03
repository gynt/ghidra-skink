
#define ADDRESS 0x401000

typedef unsigned int uint;
typedef int BOOL;

class Bar {
public:
    __declspec(noinline) BOOL foo(uint x, uint y);

    static BOOL __stdcall __foo(Bar * _this, uint x, uint y);
};

__declspec(noinline) BOOL Bar::foo(uint x, uint y) {
    return (x < 100 && y < 100) ? 1 : 0;
}

// Generic thunk template
template <typename C, typename R, typename... Args>
struct ThiscallThunk
{
    using MethodPtr  = R (C::*)(Args...);
    using ThiscallFn = R(__thiscall*)(C* thisPtr, Args...);

    static ThiscallFn make(MethodPtr m)
    {
        return reinterpret_cast<ThiscallFn&>(m);
    }
};

// Create a THISCALL pointer for foo
using foo_Method =
    ThiscallThunk<Bar, BOOL, uint, uint>;

foo_Method::ThiscallFn foo =
    foo_Method::make(&Bar::foo);

template <typename C, typename R, typename... Args>
struct MethodFromProc
{
    using ProcPtr   = R(*)(Args...);           // Free function pointer
    using MethodPtr = R(C::*)(Args...);        // Member function pointer

    static MethodPtr make(ProcPtr p)
    {
        // reinterpret_cast is valid on MSVC when the member function
        // has no 'this' adjustment (simple classes).
        return reinterpret_cast<MethodPtr&>(p);
    }
};

// Example: using a raw address from the game exe
using foo_FromProc =
    MethodFromProc<Bar, BOOL, uint, uint>;

foo_FromProc::MethodPtr fooMethod =
    foo_FromProc::make((BOOL (*)(uint, uint)) ADDRESS);

Bar instance;

BOOL __stdcall Bar::__foo(Bar * _this, uint x, uint y) {
    return (_this->*fooMethod)(x, y);
}

BOOL r4 = ((BOOL (__thiscall * const)(Bar * _this, uint x, uint y)) 0x401000)(&instance, a, b);