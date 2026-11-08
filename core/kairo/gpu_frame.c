/*
 * KairoX86#330: frame slots the presenter shows the picture from without the processor copying it (86box/kairo_gpu.h). On
 * Android each slot is a hardware buffer (AHardwareBuffer, R8G8B8A8) imported as a Vulkan image: the card's bitmap, in
 * memory the GPU shares (gpu.c), is copied into it on the GPU, and the presenter samples the buffer as a GL texture
 * (an EGLImage). The copy waits for the GPU and hands the image over to the foreign queue (GL), so the buffer holds the
 * frame once it returns. Elsewhere there are none.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include <pthread.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#define VK_NO_PROTOTYPES
#ifdef __ANDROID__
#    define VK_USE_PLATFORM_ANDROID_KHR
#    include <android/hardware_buffer.h>
#endif
#include <vulkan/vulkan.h>

#include <86box/86box.h>
#include <86box/kairo_gpu.h>

#include "gpu_internal.h"

#ifdef __ANDROID__

#    define FRAME_FUNCTIONS(F)                         \
        F(vkGetAndroidHardwareBufferPropertiesANDROID) \
        F(vkCreateImage)                               \
        F(vkDestroyImage)                              \
        F(vkAllocateMemory)                            \
        F(vkFreeMemory)                                \
        F(vkBindImageMemory)                           \
        F(vkCreateCommandPool)                         \
        F(vkDestroyCommandPool)                        \
        F(vkAllocateCommandBuffers)                    \
        F(vkBeginCommandBuffer)                        \
        F(vkEndCommandBuffer)                          \
        F(vkResetCommandBuffer)                        \
        F(vkCmdPipelineBarrier)                        \
        F(vkCmdCopyBufferToImage)                      \
        F(vkCreateFence)                               \
        F(vkDestroyFence)                              \
        F(vkResetFences)                               \
        F(vkWaitForFences)                             \
        F(vkQueueSubmit)

#    define FRAME_DECLARE(name) static PFN_##name name;
FRAME_FUNCTIONS(FRAME_DECLARE)

/* The command buffer and fence the copies share, made at the first slot; one copy at a time */
static struct {
    VkDevice        device;
    VkQueue         queue;
    uint32_t        queue_family;
    VkCommandPool   commands;
    VkCommandBuffer command;
    VkFence         done;
} frames;
static pthread_mutex_t frames_lock = PTHREAD_MUTEX_INITIALIZER;

struct kairo_gpu_frame {
    AHardwareBuffer *buffer;
    VkImage          image;
    VkDeviceMemory   memory;
    uint32_t         width, height;
    struct kairo_gpu_frame *next; /* the live slots, which kairo_gpu_close frees */
};
static struct kairo_gpu_frame *live;

static void
frame_check(VkResult result, const char *what)
{
    if (result != VK_SUCCESS)
        fatal("The PC stopped: its GPU failed (%s: Vulkan error %d)\n", what, (int) result);
}

int
kairo_gpu_frames_available(void)
{
    return kairo_gpu_on && kairo_gpu_vulkan()->android_buffers;
}

/* The device's functions and the copies' command buffer, at the first slot (frames_lock held) */
static void
frames_begin(void)
{
    if (frames.device != VK_NULL_HANDLE)
        return;
    const kairo_gpu_vulkan_t *vk = kairo_gpu_vulkan();
    if (!vk->android_buffers)
        fatal("The PC stopped: a frame slot on a GPU without Android's hardware buffers\n");
    frames.device       = (VkDevice) vk->device;
    frames.queue        = (VkQueue) vk->queue;
    frames.queue_family = vk->queue_family;
    const PFN_vkGetInstanceProcAddr instance_proc = (PFN_vkGetInstanceProcAddr) vk->get_instance_proc_addr;
    const PFN_vkGetDeviceProcAddr   device_proc
        = (PFN_vkGetDeviceProcAddr) instance_proc((VkInstance) vk->instance, "vkGetDeviceProcAddr");
    if (device_proc == NULL)
        fatal("The PC stopped: this device's Vulkan has no vkGetDeviceProcAddr\n");
#    define FRAME_LOAD(name)                                                       \
        name = (PFN_##name) device_proc(frames.device, #name);                     \
        if (name == NULL)                                                          \
            fatal("The PC stopped: this device's Vulkan has no %s\n", #name);
    FRAME_FUNCTIONS(FRAME_LOAD)
    const VkCommandPoolCreateInfo pool = { .sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO,
                                           .flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT,
                                           .queueFamilyIndex = frames.queue_family };
    frame_check(vkCreateCommandPool(frames.device, &pool, NULL, &frames.commands), "vkCreateCommandPool");
    const VkCommandBufferAllocateInfo command = { .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,
                                                  .commandPool = frames.commands, .level = VK_COMMAND_BUFFER_LEVEL_PRIMARY,
                                                  .commandBufferCount = 1 };
    frame_check(vkAllocateCommandBuffers(frames.device, &command, &frames.command), "vkAllocateCommandBuffers");
    const VkFenceCreateInfo fence = { .sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO };
    frame_check(vkCreateFence(frames.device, &fence, NULL, &frames.done), "vkCreateFence");
}

/* The slot's buffer and image let go (frames_lock held) */
static void
frame_release(struct kairo_gpu_frame *frame)
{
    if (frame->image != VK_NULL_HANDLE)
        vkDestroyImage(frames.device, frame->image, NULL);
    if (frame->memory != VK_NULL_HANDLE)
        vkFreeMemory(frames.device, frame->memory, NULL);
    if (frame->buffer != NULL)
        AHardwareBuffer_release(frame->buffer);
    frame->image  = VK_NULL_HANDLE;
    frame->memory = VK_NULL_HANDLE;
    frame->buffer = NULL;
    frame->width = frame->height = 0;
}

/* A new buffer of width x height for the slot, imported as its image (frames_lock held) */
static void
frame_make(struct kairo_gpu_frame *frame, uint32_t width, uint32_t height)
{
    frame_release(frame);
    const AHardwareBuffer_Desc desc = { .width = width, .height = height, .layers = 1,
                                        .format = AHARDWAREBUFFER_FORMAT_R8G8B8A8_UNORM,
                                        /* the presenter samples it; the screen's signature reads it, rarely */
                                        .usage = AHARDWAREBUFFER_USAGE_GPU_SAMPLED_IMAGE | AHARDWAREBUFFER_USAGE_CPU_READ_RARELY };
    if (AHardwareBuffer_allocate(&desc, &frame->buffer) != 0)
        fatal("The PC stopped: no hardware buffer for a %ux%u frame\n", width, height);

    VkAndroidHardwareBufferFormatPropertiesANDROID format = {
        .sType = VK_STRUCTURE_TYPE_ANDROID_HARDWARE_BUFFER_FORMAT_PROPERTIES_ANDROID
    };
    VkAndroidHardwareBufferPropertiesANDROID properties = { .sType = VK_STRUCTURE_TYPE_ANDROID_HARDWARE_BUFFER_PROPERTIES_ANDROID,
                                                             .pNext = &format };
    frame_check(vkGetAndroidHardwareBufferPropertiesANDROID(frames.device, frame->buffer, &properties),
                "vkGetAndroidHardwareBufferPropertiesANDROID");
    if (format.format != VK_FORMAT_R8G8B8A8_UNORM)
        fatal("The PC stopped: its GPU imports a frame's hardware buffer as format %d, not R8G8B8A8\n", (int) format.format);

    const VkExternalMemoryImageCreateInfo external = {
        .sType = VK_STRUCTURE_TYPE_EXTERNAL_MEMORY_IMAGE_CREATE_INFO,
        .handleTypes = VK_EXTERNAL_MEMORY_HANDLE_TYPE_ANDROID_HARDWARE_BUFFER_BIT_ANDROID
    };
    const VkImageCreateInfo image = { .sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO, .pNext = &external,
                                      .imageType = VK_IMAGE_TYPE_2D, .format = VK_FORMAT_R8G8B8A8_UNORM,
                                      .extent = { width, height, 1 }, .mipLevels = 1, .arrayLayers = 1,
                                      .samples = VK_SAMPLE_COUNT_1_BIT, .tiling = VK_IMAGE_TILING_OPTIMAL,
                                      .usage = VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_SAMPLED_BIT,
                                      .sharingMode = VK_SHARING_MODE_EXCLUSIVE, .initialLayout = VK_IMAGE_LAYOUT_UNDEFINED };
    frame_check(vkCreateImage(frames.device, &image, NULL, &frame->image), "vkCreateImage");

    const VkImportAndroidHardwareBufferInfoANDROID import = { .sType = VK_STRUCTURE_TYPE_IMPORT_ANDROID_HARDWARE_BUFFER_INFO_ANDROID,
                                                               .buffer = frame->buffer };
    const VkMemoryDedicatedAllocateInfo dedicated = { .sType = VK_STRUCTURE_TYPE_MEMORY_DEDICATED_ALLOCATE_INFO,
                                                      .pNext = &import, .image = frame->image };
    uint32_t type = 0;
    while ((type < 32) && !(properties.memoryTypeBits & (1u << type)))
        type++;
    if (type == 32)
        fatal("The PC stopped: its GPU has no memory type for a frame's hardware buffer\n");
    const VkMemoryAllocateInfo allocate = { .sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO, .pNext = &dedicated,
                                            .allocationSize = properties.allocationSize, .memoryTypeIndex = type };
    frame_check(vkAllocateMemory(frames.device, &allocate, NULL, &frame->memory), "vkAllocateMemory");
    frame_check(vkBindImageMemory(frames.device, frame->image, frame->memory, 0), "vkBindImageMemory");
    frame->width  = width;
    frame->height = height;
}

kairo_gpu_frame_t *
kairo_gpu_frame_new(void)
{
    struct kairo_gpu_frame *frame = calloc(1, sizeof(struct kairo_gpu_frame));
    if (frame == NULL)
        fatal("The PC stopped: no memory for a frame slot\n");
    pthread_mutex_lock(&frames_lock);
    frames_begin();
    frame->next = live;
    live        = frame;
    pthread_mutex_unlock(&frames_lock);
    return frame;
}

void
kairo_gpu_frame_free(kairo_gpu_frame_t *frame)
{
    if (frame == NULL)
        return;
    pthread_mutex_lock(&frames_lock);
    for (struct kairo_gpu_frame **at = &live; *at != NULL; at = &(*at)->next)
        if (*at == frame) {
            *at = frame->next;
            break;
        }
    frame_release(frame);
    pthread_mutex_unlock(&frames_lock);
    free(frame);
}

void *
kairo_gpu_frame_copy(kairo_gpu_frame_t *frame, const kairo_gpu_buffer_t *bitmap, size_t offset, uint32_t width,
                     uint32_t height, uint32_t pitch)
{
    if ((offset & 3) || ((offset + (((size_t) (height - 1) * pitch) + width) * 4) > bitmap->size))
        fatal("The PC stopped: a frame of %ux%u at byte %zu, %u pixels a row, outside its bitmap's %zu bytes\n", width,
              height, offset, pitch, bitmap->size);
    pthread_mutex_lock(&frames_lock);
    if ((frame->width != width) || (frame->height != height))
        frame_make(frame, width, height);

    frame_check(vkResetCommandBuffer(frames.command, 0), "vkResetCommandBuffer");
    const VkCommandBufferBeginInfo begin = { .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO,
                                             .flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT };
    frame_check(vkBeginCommandBuffer(frames.command, &begin), "vkBeginCommandBuffer");
    const VkImageSubresourceRange whole = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1 };
    /* The whole image is written: what it held before does not matter */
    const VkImageMemoryBarrier to_copy = { .sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER, .srcAccessMask = 0,
                                           .dstAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT,
                                           .oldLayout = VK_IMAGE_LAYOUT_UNDEFINED,
                                           .newLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                                           .srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
                                           .dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED, .image = frame->image,
                                           .subresourceRange = whole };
    vkCmdPipelineBarrier(frames.command, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, 0, 0, NULL, 0,
                         NULL, 1, &to_copy);
    const VkBufferImageCopy region = { .bufferOffset = offset, .bufferRowLength = pitch, .bufferImageHeight = 0,
                                       .imageSubresource = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1 },
                                       .imageOffset = { 0, 0, 0 }, .imageExtent = { width, height, 1 } };
    vkCmdCopyBufferToImage(frames.command, (VkBuffer) kairo_gpu_buffer_handle(bitmap), frame->image,
                           VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &region);
    /* Handed to the foreign queue (the presenter's GL) in the general layout */
    const VkImageMemoryBarrier to_present = { .sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,
                                              .srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT, .dstAccessMask = 0,
                                              .oldLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                                              .newLayout = VK_IMAGE_LAYOUT_GENERAL,
                                              .srcQueueFamilyIndex = frames.queue_family,
                                              .dstQueueFamilyIndex = VK_QUEUE_FAMILY_FOREIGN_EXT, .image = frame->image,
                                              .subresourceRange = whole };
    vkCmdPipelineBarrier(frames.command, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT, 0, 0, NULL,
                         0, NULL, 1, &to_present);
    frame_check(vkEndCommandBuffer(frames.command), "vkEndCommandBuffer");

    const VkSubmitInfo submit = { .sType = VK_STRUCTURE_TYPE_SUBMIT_INFO, .commandBufferCount = 1,
                                  .pCommandBuffers = &frames.command };
    frame_check(vkResetFences(frames.device, 1, &frames.done), "vkResetFences");
    kairo_gpu_queue_lock();
    const VkResult submitted = vkQueueSubmit(frames.queue, 1, &submit, frames.done);
    kairo_gpu_queue_unlock();
    frame_check(submitted, "vkQueueSubmit");
    frame_check(vkWaitForFences(frames.device, 1, &frames.done, VK_TRUE, UINT64_MAX), "vkWaitForFences");
    void *const buffer = frame->buffer;
    pthread_mutex_unlock(&frames_lock);
    return buffer;
}

void
kairo_gpu_frames_close(void)
{
    pthread_mutex_lock(&frames_lock);
    while (live != NULL) {
        struct kairo_gpu_frame *const frame = live;
        live                                = frame->next;
        frame_release(frame);
        free(frame);
    }
    if (frames.device != VK_NULL_HANDLE) {
        vkDestroyFence(frames.device, frames.done, NULL);
        vkDestroyCommandPool(frames.device, frames.commands, NULL);
    }
    memset(&frames, 0, sizeof(frames));
    pthread_mutex_unlock(&frames_lock);
}

#else /* !__ANDROID__ */

int
kairo_gpu_frames_available(void)
{
    return 0;
}

kairo_gpu_frame_t *
kairo_gpu_frame_new(void)
{
    fatal("The PC stopped: a frame slot on a host without hardware buffers\n");
    return NULL;
}

void
kairo_gpu_frame_free(kairo_gpu_frame_t *frame)
{
    (void) frame;
}

void *
kairo_gpu_frame_copy(kairo_gpu_frame_t *frame, const kairo_gpu_buffer_t *bitmap, size_t offset, uint32_t width,
                     uint32_t height, uint32_t pitch)
{
    (void) frame;
    (void) bitmap;
    (void) offset;
    (void) width;
    (void) height;
    (void) pitch;
    fatal("The PC stopped: a frame slot on a host without hardware buffers\n");
    return NULL;
}

void
kairo_gpu_frames_close(void)
{
}

#endif
