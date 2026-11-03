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

// The free firmware the app ships (docs/licensing.md), in assets/free-firmware at its place in the
// ROM set (machines/glabios/..., video/mda/...); MainActivity installs each file into the ROM folder.
// Not under roms/: the release audit forbids the ROM set's own layout in a package.
val freeFirmwareAssets = layout.buildDirectory.dir("generated/free-firmware-assets")
val stageFreeFirmware = tasks.register<Copy>("stageFreeFirmware") {
    from(rootProject.file("third_party/glabios")) {
        include("GLABIOS_0.4.0_8P.ROM", "GLABIOS_0.4.0_VP.ROM")
        into("free-firmware/machines/glabios")
    }
    from(rootProject.file("firmware/video/mda/mda.rom")) { into("free-firmware/video/mda") }
    into(freeFirmwareAssets)
}
android.sourceSets.getByName("main").assets.srcDir(freeFirmwareAssets)
tasks.named("preBuild") { dependsOn(stageFreeFirmware) }

dependencies {
    testImplementation("junit:junit:4.13.2")
}
