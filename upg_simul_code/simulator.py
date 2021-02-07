import argparse
import random
import util
from L1_cache import L1Cache
from L2_cache import L2Cache
from memory import Memory

hits = 0
misses = 0

def read(address, memory, L1_Cache, L2_Cache):
    """Read a byte from cache."""
    global hits
    global misses

    L1block = L1_Cache.read(address)
    L2block = L2_Cache.read(address)

    if L1block:
        hits += 1
        return L1block[L1_Cache.get_offset(address)]
    
    elif L2block:
            hits += 1
            return L2block[L2_Cache.get_offset(address)]

    else:
            block = memory.get_block(address)
            victim2_info = L2_Cache.load(address, block)
            victim1_info = L1_Cache.load(address, block)
            L1block = L1_Cache.read(address)
            L2block = L2_Cache.read(address)

            misses += 1

            # Write victim line's block to memory if replaced
            if victim1_info:
                memory.set_block(victim1_info[0], victim1_info[1])
            if victim2_info:
                memory.set_block(victim2_info[0], victim2_info[1])

            return L2block[L2_Cache.get_offset(address)]

def write(address, byte, memory, L1_Cache, L2_Cache):
    """Write a byte to cache."""
    L1_written = L1_Cache.write(address, byte)
    L2_written = L2_Cache.write(address, byte)

    if L1_written or L2_written:
        global hits
        hits += 1

    else:
        global misses
        misses += 1

    if args.WRITE == L1_Cache.WRITE_THROUGH:
        # Write block to memory
        block = memory.get_block(address)
        block[L1_Cache.get_offset(address)] = byte
        memory.set_block(address, block)
        
    elif args.WRITE == L1_Cache.WRITE_BACK:
        if not L1_written and not L2_written:
            # Write block to cache
            block = memory.get_block(address)
            L2_Cache.load(address, block)
            L2_Cache.write(address, byte)


replacement_policies = ["LRU", "LFU", "FIFO", "RAND"]
write_policies = ["WB", "WT"]

parser = argparse.ArgumentParser(description="Simulate the cache of a CPU.")

parser.add_argument("MEMORY", metavar="MEMORY", type=int,
                    help="Size of main memory in 2^N bytes")
parser.add_argument("L1CACHE", metavar="L1CACHE", type=int,
                    help="Size of the L1_cache in 2^N bytes")
parser.add_argument("L2CACHE", metavar="L2CACHE", type=int,
                    help="Size of the L2_cache in 2^N bytes")                   
parser.add_argument("BLOCK", metavar="BLOCK", type=int,
                    help="Size of a block of memory in 2^N bytes")
parser.add_argument("MAPPING", metavar="MAPPING", type=int,
                    help="Mapping policy for cache in 2^N ways")
parser.add_argument("REPLACE", metavar="REPLACE", choices=replacement_policies,
                    help="Replacement policy for cache {"+", ".join(replacement_policies)+"}")
parser.add_argument("WRITE", metavar="WRITE", choices=write_policies,
                    help="Write policy for cache {"+", ".join(write_policies)+"}")

args = parser.parse_args()

mem_size = 2 ** args.MEMORY
L1_cache_size = 2 ** args.L1CACHE
L2_cache_size = 2 ** args.L2CACHE
block_size = 2 ** args.BLOCK
mapping = 2 ** args.MAPPING

memory = Memory(mem_size, block_size)
L1_Cache = L1Cache(L1_cache_size, mem_size, block_size,
              mapping, args.REPLACE, args.WRITE)
L2_Cache = L2Cache(L2_cache_size, mem_size, block_size,
              mapping, args.REPLACE, args.WRITE)

mapping_str = "2^{0}-way associative".format(args.MAPPING)
print("\nMemory size: " + str(mem_size) +
      " bytes (" + str(mem_size // block_size) + " blocks)")
print("L1_Cache size: " + str(L1_cache_size) +
      " bytes (" + str(L1_cache_size // block_size) + " lines)")
print("L2_Cache size: " + str(L2_cache_size) +
      " bytes (" + str(L2_cache_size // block_size) + " lines)")      
print("Block size: " + str(block_size) + " bytes")
print("Mapping policy: " + ("direct" if mapping == 1 else mapping_str) + "\n")

command = None

while (command != "quit"):
    operation = input("> ")
    operation = operation.split()

    try:
        command = operation[0]
        params = operation[1:]

        # read
        if command == "read" and len(params) == 1:
            address = int(params[0])
            byte = read(address, memory, L1_Cache, L2_Cache)

            print("\nByte 0x" + util.hex_str(byte, 2) + " read from " +
                  util.bin_str(address, args.MEMORY) + "\n")

        # write
        elif command == "write" and len(params) == 2:
            address = int(params[0])
            byte = int(params[1])

            write(address, byte, memory, L1_Cache, L2_Cache)

            print("\nByte 0x" + util.hex_str(byte, 2) + " written to " +
                  util.bin_str(address, args.MEMORY) + "\n")

        # randread
        elif command == "randread" and len(params) == 1:
            amount = int(params[0])

            for i in range(amount):
                address = random.randint(0, mem_size - 1)
                read(address, memory, L1_Cache, L2_Cache)

            print("\n" + str(amount) + " bytes read from memory\n")

        # randwrite
        elif command == "randwrite" and len(params) == 1:
            amount = int(params[0])

            for i in range(amount):
                address = random.randint(0, mem_size - 1)
                byte = util.rand_byte()
                write(address, byte, memory, L1_Cache, L2_Cache)

            print("\n" + str(amount) + " bytes written to memory\n")

        # print L1 cache
        elif command == "printl1" and len(params) == 2:
            start = int(params[0])
            amount = int(params[1])

            L1_Cache.print_section(start, amount)

        # print L2 cache
        elif command == "printl2" and len(params) == 2:
            start = int(params[0])
            amount = int(params[1])

            L2_Cache.print_section(start, amount)

        # print memory
        elif command == "printmem" and len(params) == 2:
            start = int(params[0])
            amount = int(params[1])

            memory.print_section(start, amount)

        elif command == "stats" and len(params) == 0:
            ratio = (hits / ((hits + misses) if misses else 1)) * 100

            print("\nHits: {0} | Misses: {1}".format(hits, misses))
            print("Hit/Miss Ratio: {0:.2f}%".format(ratio) + "\n")

        elif command != "quit":
            print("\nERROR: invalid command\n")

    except IndexError:
        print("\nERROR: out of bounds\n")
    except Exception as e:
        print("\nERROR: incorrect syntax\n", e)
