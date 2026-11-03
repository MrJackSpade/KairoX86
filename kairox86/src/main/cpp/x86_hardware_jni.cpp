// The hardware 86Box offers (Kairo#143), for X86Hardware.kt: core/x86_hardware.h's answers, with a
// library copy of their own loaded on the first query and kept for the app's life.

#include <jni.h>

#include <memory>
#include <mutex>
#include <string>

#include "x86_hardware.h"

namespace {

std::mutex hardware_lock;
std::unique_ptr<kairox86::X86Hardware> hardware;
std::string hardware_roms;

std::string utf8(JNIEnv *env, jstring text) {
    const char *chars = env->GetStringUTFChars(text, nullptr);
    std::string value(chars);
    env->ReleaseStringUTFChars(text, chars);
    return value;
}

// Fails the call with [message] (a RuntimeException in Kotlin).
jstring fail(JNIEnv *env, const std::string &message) {
    env->ThrowNew(env->FindClass("java/lang/RuntimeException"), message.c_str());
    return nullptr;
}

} // namespace

extern "C" JNIEXPORT jstring JNICALL
Java_com_mrjackspade_kairox86_X86Hardware_nativeQuery(JNIEnv *env, jclass, jstring roms, jstring query) {
    std::lock_guard<std::mutex> hold(hardware_lock);
    const std::string rom_folder = utf8(env, roms);
    std::string error;
    // One ROM set for the app's life: the player's, which the app keeps in one place.
    if (hardware && hardware_roms != rom_folder) return fail(env, "The hardware queries already read the ROM set " + hardware_roms);
    if (!hardware) {
        hardware = kairox86::X86Hardware::create(rom_folder, error);
        if (!hardware) return fail(env, error);
        hardware_roms = rom_folder;
    }
    const std::string answer = hardware->query(utf8(env, query), error);
    if (answer.empty()) return fail(env, error);
    return env->NewStringUTF(answer.c_str());
}
