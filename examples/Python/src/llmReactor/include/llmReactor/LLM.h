#ifndef _llm_H
#define _llm_H
#ifndef _LLM_H // necessary for arduino-cli, which automatically includes headers that are not used
#include "pythontarget.h"
#include <limits.h>
#include "low_level_platform/api/low_level_platform.h"
#include "include/api/schedule.h"
#include "include/core/reactor.h"
#include "include/core/reactor_common.h"
#include "include/core/threaded/scheduler.h"
#include "include/core/mixed_radix.h"
#include "include/core/port.h"
#include "include/core/environment.h"
int lf_reactor_c_main(int argc, const char* argv[]);
#ifdef __cplusplus
extern "C" {
#endif
#include "../include/api/schedule.h"
#include "../include/core/reactor.h"
#ifdef __cplusplus
}
#endif
typedef struct llm_self_t{
    self_base_t base; // This field is only to be used by the runtime, not the user.
    PyObject* llm;
    PyObject* messages;
    int end[0]; // placeholder; MSVC does not compile empty structs
} llm_self_t;
typedef generic_port_instance_struct _llm_prompt_t;
typedef generic_port_instance_struct _llm_response_t;
#endif
#endif
