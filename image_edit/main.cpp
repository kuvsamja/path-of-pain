#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <sys/stat.h>
#include <unistd.h>

#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"

#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "stb_image_write.h"

int is_image_file(const char *name)
{
    const char *ext = strrchr(name, '.');
    if (!ext) return 0;

    return
        strcmp(ext, ".png") == 0 ||
        strcmp(ext, ".jpg") == 0 ||
        strcmp(ext, ".jpeg") == 0;
}

void remove_red(unsigned char *img, int w, int h)
{
    int pixels = w * h;
    for (int i = 0; i < pixels; i++) {
        unsigned char *p = &img[i * 4];
        if (p[0] > 200 && p[1] < 100 && p[2] < 100) {
            p[3] = 0;
        }
    }
}

void process_image(const char *in, const char *out)
{
    int w, h, c;
    unsigned char *img = stbi_load(in, &w, &h, &c, 4);
    if (!img) {
        printf("Failed: %s\n", in);
        return;
    }

    remove_red(img, w, h);
    stbi_write_png(out, w, h, 4, img, w * 4);
    stbi_image_free(img);

    printf("Processed: %s\n", in);
}

void process_directory(const char *in_dir, const char *out_dir)
{
    DIR *dir = opendir(in_dir);
    if (!dir) return;

    mkdir(out_dir, 0755);

    struct dirent *e;
    while ((e = readdir(dir)) != NULL) {
        if (!strcmp(e->d_name, ".") || !strcmp(e->d_name, ".."))
            continue;

        char in_path[1024];
        char out_path[1024];

        snprintf(in_path, sizeof(in_path), "%s/%s", in_dir, e->d_name);
        snprintf(out_path, sizeof(out_path), "%s/%s", out_dir, e->d_name);

        if (e->d_type == DT_DIR) {
            process_directory(in_path, out_path);
        }
        else if (e->d_type == DT_REG && is_image_file(e->d_name)) {
            strcat(out_path, "");
            process_image(in_path, out_path);
        }
    }

    closedir(dir);
}

int main(int argc, char **argv)
{
    if (argc != 3) {
        printf("Usage: %s input_folder output_folder\n", argv[0]);
        return 1;
    }

    process_directory(argv[1], argv[2]);
    return 0;
}
