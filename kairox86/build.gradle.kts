plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

extra["kairoProduct"] = "kairox86"
extra["kairoLabel"] = "KairoX86"
extra["kairoCatalogRules"] = "com.mrjackspade.kairox86.X86Catalog"
apply(from = rootProject.file("shared/gradle/kairo-app.gradle"))

// 86Box's own library (core/CMakeLists.txt), which the app's library loads afresh for each machine.
android.defaultConfig.externalNativeBuild.cmake.targets.add("86Box")

dependencies {
    testImplementation("junit:junit:4.13.2")
}
