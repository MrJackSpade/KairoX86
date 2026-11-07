/*
 * The machine's GPU (KairoX86#232, gpu.h): Vulkan 1.1 compute, through the system's Vulkan library
 * loaded at the machine's start (libvulkan.so on Android, vulkan-1.dll on Windows), with the pinned
 * Khronos headers (third_party/vulkan-headers).
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include <pthread.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <time.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#    include <windows.h>
#else
#    include <dlfcn.h>
#endif

#define VK_NO_PROTOTYPES
#include <vulkan/vulkan.h>

#include <86box/86box.h>
#include <86box/config.h>

#include <86box/kairo_gpu.h>

#include "gpu_internal.h"

bool kairo_gpu_on;

/* The Vulkan functions the backend calls: the loader's, the instance's and the device's. */
#define KAIRO_VK_INSTANCE_FUNCTIONS(F)            \
    F(vkDestroyInstance)                          \
    F(vkEnumeratePhysicalDevices)                 \
    F(vkGetPhysicalDeviceProperties)              \
    F(vkGetPhysicalDeviceQueueFamilyProperties)   \
    F(vkGetPhysicalDeviceMemoryProperties)        \
    F(vkCreateDevice)                             \
    F(vkGetDeviceProcAddr)                        \
    F(vkGetPhysicalDeviceFeatures2)               \
    F(vkEnumerateDeviceExtensionProperties)

#define KAIRO_VK_DEVICE_FUNCTIONS(F)       \
    F(vkDestroyDevice)                     \
    F(vkGetDeviceQueue)                    \
    F(vkCreateBuffer)                      \
    F(vkDestroyBuffer)                     \
    F(vkGetBufferMemoryRequirements)       \
    F(vkAllocateMemory)                    \
    F(vkFreeMemory)                        \
    F(vkBindBufferMemory)                  \
    F(vkMapMemory)                         \
    F(vkCreateShaderModule)                \
    F(vkDestroyShaderModule)               \
    F(vkCreateDescriptorSetLayout)         \
    F(vkDestroyDescriptorSetLayout)        \
    F(vkCreatePipelineLayout)              \
    F(vkDestroyPipelineLayout)             \
    F(vkCreateComputePipelines)            \
    F(vkDestroyPipeline)                   \
    F(vkCreateDescriptorPool)              \
    F(vkDestroyDescriptorPool)             \
    F(vkAllocateDescriptorSets)            \
    F(vkUpdateDescriptorSets)              \
    F(vkCreateCommandPool)                 \
    F(vkDestroyCommandPool)                \
    F(vkAllocateCommandBuffers)            \
    F(vkBeginCommandBuffer)                \
    F(vkEndCommandBuffer)                  \
    F(vkResetCommandBuffer)                \
    F(vkCmdBindPipeline)                   \
    F(vkCmdBindDescriptorSets)             \
    F(vkCmdPushConstants)                  \
    F(vkCmdDispatch)                       \
    F(vkCmdPipelineBarrier)                \
    F(vkCreateFence)                       \
    F(vkDestroyFence)                      \
    F(vkResetFences)                       \
    F(vkWaitForFences)                     \
    F(vkQueueSubmit)

#define KAIRO_VK_DECLARE(name) static PFN_##name name;
static PFN_vkGetInstanceProcAddr vkGetInstanceProcAddr;
static PFN_vkCreateInstance      vkCreateInstance;
KAIRO_VK_INSTANCE_FUNCTIONS(KAIRO_VK_DECLARE)
KAIRO_VK_DEVICE_FUNCTIONS(KAIRO_VK_DECLARE)

static struct {
    void            *library;
    VkInstance       instance;
    VkPhysicalDevice physical;
    VkDevice         device;
    uint32_t         queue_family;
    VkQueue          queue;
    uint32_t         memory_type; /* host-visible and coherent */
    VkCommandPool    commands;
    VkCommandBuffer  command;
    VkFence          done;
    char             name[VK_MAX_PHYSICAL_DEVICE_NAME_SIZE];
    kairo_gpu_vulkan_t vulkan; /* KairoX86#239: the handles a card's own Vulkan backend works with */
} gpu;

/* KairoX86#239: every submit to the queue, the core's and a card backend's, holds this (Vulkan's queue is
   externally synchronised) */
static pthread_mutex_t queue_lock = PTHREAD_MUTEX_INITIALIZER;

const kairo_gpu_vulkan_t *
kairo_gpu_vulkan(void)
{
    return &gpu.vulkan;
}

void
kairo_gpu_queue_lock(void)
{
    pthread_mutex_lock(&queue_lock);
}

void
kairo_gpu_queue_unlock(void)
{
    pthread_mutex_unlock(&queue_lock);
}

/* One kernel runs at a time: they share the command buffer and the fence (callers are the card's
   threads: the CPU's, a renderer's, the blit's). */
static pthread_mutex_t run_lock = PTHREAD_MUTEX_INITIALIZER;

struct kairo_gpu_kernel {
    const char           *name;
    int                   buffers;
    uint32_t              push_bytes;
    VkDescriptorSetLayout set_layout;
    VkPipelineLayout      layout;
    VkPipeline            pipeline;
    VkDescriptorPool      pool;
    VkDescriptorSet       set;
};

typedef struct {
    VkBuffer       buffer;
    VkDeviceMemory memory;
} buffer_impl_t;

/* Ends the machine: what failed, and Vulkan's result. */
static void
vk_check(VkResult result, const char *what)
{
    if (result != VK_SUCCESS)
        fatal("The PC stopped: its GPU failed (%s: Vulkan error %d)\n", what, (int) result);
}

static void *
library_open(void)
{
#ifdef _WIN32
    return (void *) LoadLibraryA("vulkan-1.dll");
#else
    return dlopen("libvulkan.so", RTLD_NOW | RTLD_LOCAL);
#endif
}

static void *
library_function(const char *name)
{
#ifdef _WIN32
    return (void *) GetProcAddress((HMODULE) gpu.library, name);
#else
    return dlsym(gpu.library, name);
#endif
}

static void
library_close(void)
{
#ifdef _WIN32
    FreeLibrary((HMODULE) gpu.library);
#else
    dlclose(gpu.library);
#endif
}

/* The first queue family with compute. */
static bool
compute_family(VkPhysicalDevice physical, uint32_t *family)
{
    uint32_t count = 0;
    vkGetPhysicalDeviceQueueFamilyProperties(physical, &count, NULL);
    VkQueueFamilyProperties families[16];
    if (count > 16)
        count = 16;
    vkGetPhysicalDeviceQueueFamilyProperties(physical, &count, families);
    for (uint32_t i = 0; i < count; i++)
        if (families[i].queueFlags & VK_QUEUE_COMPUTE_BIT) {
            *family = i;
            return true;
        }
    return false;
}

void
kairo_gpu_open(void)
{
    kairo_gpu_on = config_kairo_int("hardware_acceleration", 0) != 0;
    if (!kairo_gpu_on)
        return;

    gpu.library = library_open();
    if (gpu.library == NULL)
        fatal("The PC stopped: Hardware acceleration is on, and this device has no Vulkan\n");
    vkGetInstanceProcAddr = (PFN_vkGetInstanceProcAddr) library_function("vkGetInstanceProcAddr");
    if (vkGetInstanceProcAddr == NULL)
        fatal("The PC stopped: this device's Vulkan library has no vkGetInstanceProcAddr\n");
    vkCreateInstance = (PFN_vkCreateInstance) vkGetInstanceProcAddr(NULL, "vkCreateInstance");

    const VkApplicationInfo app = { .sType = VK_STRUCTURE_TYPE_APPLICATION_INFO, .pApplicationName = "KairoX86",
                                    .apiVersion = VK_API_VERSION_1_1 };
    const VkInstanceCreateInfo instance_info = { .sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO, .pApplicationInfo = &app };
    vk_check(vkCreateInstance(&instance_info, NULL, &gpu.instance), "vkCreateInstance");
#define KAIRO_VK_LOAD_INSTANCE(name)                                                    \
    name = (PFN_##name) vkGetInstanceProcAddr(gpu.instance, #name);                     \
    if (name == NULL)                                                                   \
        fatal("The PC stopped: this device's Vulkan has no %s\n", #name);
    KAIRO_VK_INSTANCE_FUNCTIONS(KAIRO_VK_LOAD_INSTANCE)

    /* The first GPU with compute, a discrete one before any other (a PC with two) */
    uint32_t count = 0;
    vk_check(vkEnumeratePhysicalDevices(gpu.instance, &count, NULL), "vkEnumeratePhysicalDevices");
    VkPhysicalDevice physicals[8];
    if (count > 8)
        count = 8;
    vk_check(vkEnumeratePhysicalDevices(gpu.instance, &count, physicals), "vkEnumeratePhysicalDevices");
    bool found = false;
    for (int pass = 0; (pass < 2) && !found; pass++)
        for (uint32_t i = 0; (i < count) && !found; i++) {
            VkPhysicalDeviceProperties properties;
            vkGetPhysicalDeviceProperties(physicals[i], &properties);
            const bool discrete = properties.deviceType == VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU;
            if ((properties.apiVersion >= VK_API_VERSION_1_1) && (discrete || (pass == 1))
                && compute_family(physicals[i], &gpu.queue_family)) {
                gpu.physical = physicals[i];
                found        = true;
                snprintf(gpu.name, sizeof(gpu.name), "%s", properties.deviceName);
            }
        }
    if (!found)
        fatal("The PC stopped: Hardware acceleration is on, and this device has no Vulkan 1.1 GPU with compute\n");

    VkPhysicalDeviceMemoryProperties memory;
    vkGetPhysicalDeviceMemoryProperties(gpu.physical, &memory);
    /* Cached for the processor too: the CPU reads these buffers as much as it writes them (a bitmap the
       card draws on and the frame is copied from), and uncached memory (a discrete GPU's own, over its
       bus) makes every read a bus transfer */
    const VkMemoryPropertyFlags wanted = VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT
                                         | VK_MEMORY_PROPERTY_HOST_CACHED_BIT;
    gpu.memory_type = UINT32_MAX;
    for (uint32_t i = 0; (i < memory.memoryTypeCount) && (gpu.memory_type == UINT32_MAX); i++)
        if ((memory.memoryTypes[i].propertyFlags & wanted) == wanted)
            gpu.memory_type = i;
    if (gpu.memory_type == UINT32_MAX)
        fatal("The PC stopped: its GPU has no memory the processor can share and cache\n");

    /* KairoX86#239: what a card's own Vulkan backend needs on this device (the Rage 128's: 64-bit integers, 16-bit
       storage access, host memory imported), turned on where the GPU has it; the card asks for it at its start */
    VkPhysicalDevice16BitStorageFeatures storage16 = { .sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_16BIT_STORAGE_FEATURES };
    VkPhysicalDeviceFeatures2            has       = { .sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FEATURES_2, .pNext = &storage16 };
    vkGetPhysicalDeviceFeatures2(gpu.physical, &has);
    gpu.vulkan.int64     = has.features.shaderInt64;
    gpu.vulkan.storage16 = storage16.storageBuffer16BitAccess;
    uint32_t extensions = 0;
    vk_check(vkEnumerateDeviceExtensionProperties(gpu.physical, NULL, &extensions, NULL), "vkEnumerateDeviceExtensionProperties");
    VkExtensionProperties *extension = calloc(extensions ? extensions : 1, sizeof(VkExtensionProperties));
    if (extension == NULL)
        fatal("The PC stopped: no memory for the GPU's extensions\n");
    vk_check(vkEnumerateDeviceExtensionProperties(gpu.physical, NULL, &extensions, extension), "vkEnumerateDeviceExtensionProperties");
    for (uint32_t i = 0; i < extensions; i++)
        if (!strcmp(extension[i].extensionName, VK_EXT_EXTERNAL_MEMORY_HOST_EXTENSION_NAME))
            gpu.vulkan.host_memory = 1;
    free(extension);
    VkPhysicalDevice16BitStorageFeatures storage16_on = { .sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_16BIT_STORAGE_FEATURES,
                                                          .storageBuffer16BitAccess = storage16.storageBuffer16BitAccess };
    VkPhysicalDeviceFeatures2            on           = { .sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FEATURES_2, .pNext = &storage16_on };
    on.features.shaderInt64 = has.features.shaderInt64;
    const char *const host_memory = VK_EXT_EXTERNAL_MEMORY_HOST_EXTENSION_NAME;

    const float                   priority   = 1.0f;
    const VkDeviceQueueCreateInfo queue_info = { .sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO,
                                                 .queueFamilyIndex = gpu.queue_family, .queueCount = 1,
                                                 .pQueuePriorities = &priority };
    const VkDeviceCreateInfo device_info = { .sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO, .pNext = &on, .queueCreateInfoCount = 1,
                                             .pQueueCreateInfos = &queue_info,
                                             .enabledExtensionCount = gpu.vulkan.host_memory ? 1u : 0u,
                                             .ppEnabledExtensionNames = gpu.vulkan.host_memory ? &host_memory : NULL };
    vk_check(vkCreateDevice(gpu.physical, &device_info, NULL, &gpu.device), "vkCreateDevice");
#define KAIRO_VK_LOAD_DEVICE(name)                                                      \
    name = (PFN_##name) vkGetDeviceProcAddr(gpu.device, #name);                         \
    if (name == NULL)                                                                   \
        fatal("The PC stopped: this device's Vulkan has no %s\n", #name);
    KAIRO_VK_DEVICE_FUNCTIONS(KAIRO_VK_LOAD_DEVICE)
    vkGetDeviceQueue(gpu.device, gpu.queue_family, 0, &gpu.queue);
    gpu.vulkan.get_instance_proc_addr = (void *) vkGetInstanceProcAddr;
    gpu.vulkan.instance               = gpu.instance;
    gpu.vulkan.physical               = gpu.physical;
    gpu.vulkan.device                 = gpu.device;
    gpu.vulkan.queue_family           = gpu.queue_family;
    gpu.vulkan.queue                  = gpu.queue;

    const VkCommandPoolCreateInfo pool_info = { .sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO,
                                                .flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT,
                                                .queueFamilyIndex = gpu.queue_family };
    vk_check(vkCreateCommandPool(gpu.device, &pool_info, NULL, &gpu.commands), "vkCreateCommandPool");
    const VkCommandBufferAllocateInfo command_info = { .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,
                                                       .commandPool = gpu.commands,
                                                       .level = VK_COMMAND_BUFFER_LEVEL_PRIMARY, .commandBufferCount = 1 };
    vk_check(vkAllocateCommandBuffers(gpu.device, &command_info, &gpu.command), "vkAllocateCommandBuffers");
    const VkFenceCreateInfo fence_info = { .sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO };
    vk_check(vkCreateFence(gpu.device, &fence_info, NULL, &gpu.done), "vkCreateFence");
}

const char *
kairo_gpu_name(void)
{
    return gpu.name;
}

void
kairo_gpu_close(void)
{
    if (gpu.device != VK_NULL_HANDLE) {
        kairo_gpu_scanout_close();
        kairo_gpu_voodoo_close();
        kairo_gpu_virge_close();
        kairo_gpu_mach64_close();
        kairo_gpu_powervr_close();
        vkDestroyFence(gpu.device, gpu.done, NULL);
        vkDestroyCommandPool(gpu.device, gpu.commands, NULL);
        vkDestroyDevice(gpu.device, NULL);
    }
    if (gpu.instance != VK_NULL_HANDLE)
        vkDestroyInstance(gpu.instance, NULL);
    if (gpu.library != NULL)
        library_close();
    memset(&gpu, 0, sizeof(gpu));
    kairo_gpu_on = false;
}

kairo_gpu_buffer_t *
kairo_gpu_buffer(size_t size)
{
    kairo_gpu_buffer_t *buffer = calloc(1, sizeof(kairo_gpu_buffer_t));
    buffer_impl_t      *impl   = calloc(1, sizeof(buffer_impl_t));
    if ((buffer == NULL) || (impl == NULL))
        fatal("The PC stopped: no memory for a GPU buffer\n");
    const VkBufferCreateInfo info = { .sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO, .size = size,
                                      /* copies too: a card's own backend (KairoX86#239) mirrors from and to it */
                                      .usage = VK_BUFFER_USAGE_STORAGE_BUFFER_BIT | VK_BUFFER_USAGE_TRANSFER_SRC_BIT
                                               | VK_BUFFER_USAGE_TRANSFER_DST_BIT,
                                      .sharingMode = VK_SHARING_MODE_EXCLUSIVE };
    vk_check(vkCreateBuffer(gpu.device, &info, NULL, &impl->buffer), "vkCreateBuffer");
    VkMemoryRequirements needs;
    vkGetBufferMemoryRequirements(gpu.device, impl->buffer, &needs);
    if (!(needs.memoryTypeBits & (1u << gpu.memory_type)))
        fatal("The PC stopped: its GPU cannot keep a buffer in memory the processor shares\n");
    const VkMemoryAllocateInfo allocate = { .sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
                                            .allocationSize = needs.size, .memoryTypeIndex = gpu.memory_type };
    vk_check(vkAllocateMemory(gpu.device, &allocate, NULL, &impl->memory), "vkAllocateMemory");
    vk_check(vkBindBufferMemory(gpu.device, impl->buffer, impl->memory, 0), "vkBindBufferMemory");
    vk_check(vkMapMemory(gpu.device, impl->memory, 0, VK_WHOLE_SIZE, 0, &buffer->data), "vkMapMemory");
    memset(buffer->data, 0, size);
    buffer->size = size;
    buffer->impl = impl;
    return buffer;
}

uint64_t
kairo_gpu_buffer_handle(const kairo_gpu_buffer_t *buffer)
{
    return (uint64_t) ((const buffer_impl_t *) buffer->impl)->buffer;
}

void
kairo_gpu_buffer_free(kairo_gpu_buffer_t *buffer)
{
    if (buffer == NULL)
        return;
    buffer_impl_t *impl = buffer->impl;
    vkDestroyBuffer(gpu.device, impl->buffer, NULL);
    vkFreeMemory(gpu.device, impl->memory, NULL);
    free(impl);
    free(buffer);
}

/* The card memory allocated (kairo_gpu_alloc), found by where it starts */
#define CARD_MEMORY_MAX 64
static kairo_gpu_buffer_t *card_memory[CARD_MEMORY_MAX];
static pthread_mutex_t     card_memory_lock = PTHREAD_MUTEX_INITIALIZER;

void *
kairo_gpu_alloc(size_t size)
{
    kairo_gpu_buffer_t *buffer = kairo_gpu_buffer(size);
    pthread_mutex_lock(&card_memory_lock);
    int i = 0;
    while ((i < CARD_MEMORY_MAX) && (card_memory[i] != NULL))
        i++;
    if (i == CARD_MEMORY_MAX)
        fatal("The PC stopped: more than %d blocks of card memory on the GPU\n", CARD_MEMORY_MAX);
    card_memory[i] = buffer;
    pthread_mutex_unlock(&card_memory_lock);
    return buffer->data;
}

kairo_gpu_buffer_t *
kairo_gpu_buffer_of(const void *data)
{
    kairo_gpu_buffer_t *found = NULL;
    pthread_mutex_lock(&card_memory_lock);
    for (int i = 0; (i < CARD_MEMORY_MAX) && (found == NULL); i++)
        if ((card_memory[i] != NULL) && (card_memory[i]->data == data))
            found = card_memory[i];
    pthread_mutex_unlock(&card_memory_lock);
    if (found == NULL)
        fatal("The PC stopped: card memory the GPU does not share\n");
    return found;
}

void
kairo_gpu_free(void *data)
{
    if (data == NULL)
        return;
    kairo_gpu_buffer_t *buffer = kairo_gpu_buffer_of(data);
    pthread_mutex_lock(&card_memory_lock);
    for (int i = 0; i < CARD_MEMORY_MAX; i++)
        if (card_memory[i] == buffer)
            card_memory[i] = NULL;
    pthread_mutex_unlock(&card_memory_lock);
    kairo_gpu_buffer_free(buffer);
}

kairo_gpu_kernel_t *
kairo_gpu_kernel(const char *name, const uint32_t *spirv, size_t spirv_bytes, int buffers, uint32_t push_bytes)
{
    if ((buffers < 1) || (buffers > 8) || (push_bytes > 128))
        fatal("GPU kernel %s: %d buffers and %u bytes of push constants\n", name, buffers, (unsigned) push_bytes);
    kairo_gpu_kernel_t *kernel = calloc(1, sizeof(kairo_gpu_kernel_t));
    if (kernel == NULL)
        fatal("The PC stopped: no memory for a GPU kernel\n");
    kernel->name       = name;
    kernel->buffers    = buffers;
    kernel->push_bytes = push_bytes;

    VkDescriptorSetLayoutBinding bindings[8];
    for (int i = 0; i < buffers; i++)
        bindings[i] = (VkDescriptorSetLayoutBinding) { .binding = (uint32_t) i,
                                                       .descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,
                                                       .descriptorCount = 1, .stageFlags = VK_SHADER_STAGE_COMPUTE_BIT };
    const VkDescriptorSetLayoutCreateInfo set_info = { .sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO,
                                                       .bindingCount = (uint32_t) buffers, .pBindings = bindings };
    vk_check(vkCreateDescriptorSetLayout(gpu.device, &set_info, NULL, &kernel->set_layout), name);
    const VkPushConstantRange push = { .stageFlags = VK_SHADER_STAGE_COMPUTE_BIT, .size = push_bytes };
    const VkPipelineLayoutCreateInfo layout_info = { .sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO,
                                                     .setLayoutCount = 1, .pSetLayouts = &kernel->set_layout,
                                                     .pushConstantRangeCount = push_bytes ? 1 : 0,
                                                     .pPushConstantRanges = push_bytes ? &push : NULL };
    vk_check(vkCreatePipelineLayout(gpu.device, &layout_info, NULL, &kernel->layout), name);

    const VkShaderModuleCreateInfo module_info = { .sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO,
                                                   .codeSize = spirv_bytes, .pCode = spirv };
    VkShaderModule module;
    vk_check(vkCreateShaderModule(gpu.device, &module_info, NULL, &module), name);
    const VkComputePipelineCreateInfo pipeline_info = {
        .sType  = VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO,
        .stage  = { .sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO, .stage = VK_SHADER_STAGE_COMPUTE_BIT,
                    .module = module, .pName = "main" },
        .layout = kernel->layout
    };
    /* How long the driver takes to build it, reported: a kernel that builds slowly stalls the machine where it is
       first used (KairoX86#237: one kernel took minutes until its heavy functions had one call site each) */
    struct timespec built_from, built_to;
    clock_gettime(CLOCK_MONOTONIC, &built_from);
    const VkResult made = vkCreateComputePipelines(gpu.device, VK_NULL_HANDLE, 1, &pipeline_info, NULL, &kernel->pipeline);
    clock_gettime(CLOCK_MONOTONIC, &built_to);
    vkDestroyShaderModule(gpu.device, module, NULL);
    vk_check(made, name);
    fprintf(stderr, "kairo-gpu: kernel %s built in %.0f ms\n", name,
            (double) (built_to.tv_sec - built_from.tv_sec) * 1e3 + (double) (built_to.tv_nsec - built_from.tv_nsec) / 1e6);

    const VkDescriptorPoolSize       pool_size = { .type = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER, .descriptorCount = (uint32_t) buffers };
    const VkDescriptorPoolCreateInfo pool_info = { .sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO, .maxSets = 1,
                                                   .poolSizeCount = 1, .pPoolSizes = &pool_size };
    vk_check(vkCreateDescriptorPool(gpu.device, &pool_info, NULL, &kernel->pool), name);
    const VkDescriptorSetAllocateInfo set_allocate = { .sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO,
                                                       .descriptorPool = kernel->pool, .descriptorSetCount = 1,
                                                       .pSetLayouts = &kernel->set_layout };
    vk_check(vkAllocateDescriptorSets(gpu.device, &set_allocate, &kernel->set), name);
    return kernel;
}

void
kairo_gpu_kernel_free(kairo_gpu_kernel_t *kernel)
{
    if (kernel == NULL)
        return;
    vkDestroyDescriptorPool(gpu.device, kernel->pool, NULL);
    vkDestroyPipeline(gpu.device, kernel->pipeline, NULL);
    vkDestroyPipelineLayout(gpu.device, kernel->layout, NULL);
    vkDestroyDescriptorSetLayout(gpu.device, kernel->set_layout, NULL);
    free(kernel);
}

void
kairo_gpu_run(kairo_gpu_kernel_t *kernel, kairo_gpu_buffer_t *const *buffers, const void *push, uint32_t groups_x,
              uint32_t groups_y, uint32_t groups_z)
{
    pthread_mutex_lock(&run_lock);
    VkDescriptorBufferInfo infos[8];
    VkWriteDescriptorSet   writes[8];
    for (int i = 0; i < kernel->buffers; i++) {
        infos[i]  = (VkDescriptorBufferInfo) { .buffer = ((buffer_impl_t *) buffers[i]->impl)->buffer, .range = VK_WHOLE_SIZE };
        writes[i] = (VkWriteDescriptorSet) { .sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET, .dstSet = kernel->set,
                                             .dstBinding = (uint32_t) i, .descriptorCount = 1,
                                             .descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER, .pBufferInfo = &infos[i] };
    }
    vkUpdateDescriptorSets(gpu.device, (uint32_t) kernel->buffers, writes, 0, NULL);

    vk_check(vkResetCommandBuffer(gpu.command, 0), kernel->name);
    const VkCommandBufferBeginInfo begin = { .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO,
                                             .flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT };
    vk_check(vkBeginCommandBuffer(gpu.command, &begin), kernel->name);
    vkCmdBindPipeline(gpu.command, VK_PIPELINE_BIND_POINT_COMPUTE, kernel->pipeline);
    vkCmdBindDescriptorSets(gpu.command, VK_PIPELINE_BIND_POINT_COMPUTE, kernel->layout, 0, 1, &kernel->set, 0, NULL);
    if (kernel->push_bytes)
        vkCmdPushConstants(gpu.command, kernel->layout, VK_SHADER_STAGE_COMPUTE_BIT, 0, kernel->push_bytes, push);
    vkCmdDispatch(gpu.command, groups_x, groups_y, groups_z);
    /* What the kernel wrote, visible to the processor once the fence signals */
    const VkMemoryBarrier to_host = { .sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER, .srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT,
                                      .dstAccessMask = VK_ACCESS_HOST_READ_BIT };
    vkCmdPipelineBarrier(gpu.command, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, VK_PIPELINE_STAGE_HOST_BIT, 0, 1, &to_host, 0,
                         NULL, 0, NULL);
    vk_check(vkEndCommandBuffer(gpu.command), kernel->name);

    const VkSubmitInfo submit = { .sType = VK_STRUCTURE_TYPE_SUBMIT_INFO, .commandBufferCount = 1,
                                  .pCommandBuffers = &gpu.command };
    vk_check(vkResetFences(gpu.device, 1, &gpu.done), kernel->name);
    kairo_gpu_queue_lock();
    const VkResult submitted = vkQueueSubmit(gpu.queue, 1, &submit, gpu.done);
    kairo_gpu_queue_unlock();
    vk_check(submitted, kernel->name);
    vk_check(vkWaitForFences(gpu.device, 1, &gpu.done, VK_TRUE, UINT64_MAX), kernel->name);
    pthread_mutex_unlock(&run_lock);
}
