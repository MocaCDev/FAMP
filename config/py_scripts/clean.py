import subprocess
import os
import yaml

# `boot.yaml` data
yaml_data = None

# Obtain the yaml data from `boot.yaml`
with open('../boot.yaml', 'r') as file:
    yaml_data = yaml.full_load(file)
    file.close()

# Delete all binaries
subprocess.run(f'rm -rf ../{yaml_data["bin_folder"]}/*.bin', shell=True, cwd=os.getcwd())
subprocess.run(f'rm -rf ../{yaml_data["bin_folder"]}/*.o', shell=True, cwd=os.getcwd())
subprocess.run(f'rm -rf ../{yaml_data["bin_folder"]}/*.out', shell=True, cwd=os.getcwd())
subprocess.run(f'rm -rf ../{yaml_data["bin_folder"]}/*.image', shell=True, cwd=os.getcwd())

# Delete the bootloader
subprocess.run('rm -rf boot/boot.s', shell=True, cwd=os.getcwd())

# Delete all local binaries
subprocess.run('rm -rf bin/*.o', shell=True, cwd=os.getcwd())
subprocess.run('rm -rf bin/*.bin', shell=True, cwd=os.getcwd())

# This is needed so we can have "{FLAGS}" put in after `@gcc`
flags = '{FLAGS}'

# Rewrite the original Makefile
with open('Makefile', 'w') as f:
    f.write(f'''.PHONY: build
.PHONY: mbr_partition_table
.PHONY: higher_half_kernel_program

FLAGS = -masm=intel -O1 -Wno-error -c -nostdinc -nostdlib -fno-builtin -fno-stack-protector -ffreestanding -m32
build: mbr_partition_table higher_half_kernel_program
	@chmod +x config/scripts/*
	@nasm protocol/protocol_util.s -f elf32 -o ../bin/protocol_util.o
	@gcc ${flags} -o bin/second_stage.o boot/second_stage.c
	@gcc ${flags} -o ../{yaml_data["kernel_o_binary"]} ../{yaml_data["kernel_source_code_file"]}
	@ld -m elf_i386 -Tlinker/linker.ld -nostdlib --nmagic -o bin/boot.out bin/second_stage.o ../bin/protocol_util.o
	@ld -m elf_i386 -Tlinker/kernel.ld -nostdlib --nmagic -o ../bin/kernel.out ../{yaml_data["kernel_o_binary"]} ../bin/protocol_util.o
	@objcopy -O binary bin/boot.out bin/second_stage.bin
	@objcopy -O binary ../bin/kernel.out ../{yaml_data["kernel_bin_filename"]}
	@./bin/format.o bin/second_stage.bin --second_stage
	@./bin/format.o ../{yaml_data["kernel_bin_filename"]} --kernel
	@cd config && make build
	
mbr_partition_table:
	@gcc config/format.c -o bin/format.o
	@nasm boot/partition_util.s -f elf32 -o bin/partition_util.o
	@gcc ${flags} -o bin/mbr_partition_table.o -c boot/mbr_partition_table.c
	@ld -m elf_i386 -Tboot/mbr_partition_table.ld -nostdlib --nmagic -o bin/mbr_partition_table.out bin/mbr_partition_table.o bin/partition_util.o
	@objcopy -O binary bin/mbr_partition_table.out bin/mbr_partition_table.bin
	@./bin/format.o bin/mbr_partition_table.bin --jpad
 
higher_half_kernel_program:
	@gcc ${flags} -o bin/higher_half_kernel.o -c boot/higher_half_kernel.c
	@ld -m elf_i386 -Tboot/higher_half_kernel.ld -nostdlib --nmagic -o bin/higher_half_kernel.out bin/higher_half_kernel.o
	@objcopy -O binary bin/higher_half_kernel.out bin/higher_half_kernel.bin
	@./bin/format.o bin/higher_half_kernel.bin --jpad''')
    f.close()
