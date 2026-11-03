apply(from = "shared/gradle/android-settings.gradle")

rootProject.name = "KairoX86"
include(":kairox86", ":frontend")
project(":frontend").projectDir = file("shared/frontend")
