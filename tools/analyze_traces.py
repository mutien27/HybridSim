import sys

SET_SIZE = 64
PAGE_SIZE = 4096
CACHE_PAGES = 131072
TOTAL_PAGES = 2097152
BURST_SIZE = 64

NUM_SETS = CACHE_PAGES / SET_SIZE

def PAGE_NUMBER(addr):
	return addr / PAGE_SIZE
def PAGE_ADDRESS(addr):
	return ((addr / PAGE_SIZE) * PAGE_SIZE)
def PAGE_OFFSET(addr):
	return (addr % PAGE_SIZE)
def SET_INDEX(addr):
	return (PAGE_NUMBER(addr) % NUM_SETS)
def TAG(addr):
	return (PAGE_NUMBER(addr) / NUM_SETS)
def FLASH_ADDRESS(tag, set_num):
	return ((tag * NUM_SETS + set_num) * PAGE_SIZE)
def ALIGN(addr):
	return (((addr / BURST_SIZE) * BURST_SIZE) % (TOTAL_PAGES * PAGE_SIZE))


def process_tracefile(filename):
	tracefile = open(filename, 'r')


	counter = 0
	cnt = {}
	cache = {}
	prefetch = {}

	for i in range(NUM_SETS):
		cnt[i] = 0 # This counts the access number to each set (which is used to trigger prefetches)
		cache[i] = [] # This holds SET_SIZE pairs of (access number, page) in LRU order (the one at the end gets evicted on misses).
		prefetch[i] = [] # This holds triples of (access number, old page, new page) to prefetch. These are triggered immediately after a set is no longer needed.


	# The general algorithm here is that whenever a miss occurs, we know when a particular evicted page is no longer needed (by using its access number).
	# Since we have the last access number a particular page was actually used, we can evict the page immediately after that access rather than waiting
	# until later.
	# The prefetch lists (one for each set) contains all of the data necessary to do this early eviction and prefetching.

	while(1):
		line = tracefile.readline()
		if line == '':
			break

		[cycle, op, address] = [int(i) for i in line.strip().split()]
		address = ALIGN(address)

		page = PAGE_ADDRESS(address)
		set_index = SET_INDEX(address)


		# Check for a hit.
		set_pages = [i for (i,j) in cache[set_index]]
		if set_pages.count(page) == 1:
			# We hit.

			# Find and delete the old cache entry for this page.
			page_index = set_pages.index(page)
			del cache[set_index][page_index]

		else:
			# We missed.

			if len(cache[set_index]) == SET_SIZE:
				# Evict the last thing in the cache (index 63).
				evicted = cache[set_index].pop(63)
				(evicted_page, access_number) = evicted

				# Update the prefetch list.
				prefetch[set_index].append((access_number, evicted_page, page))

			else:
				# The cache set isn't full yet, so just put this at the front of the list and do not evict anything.
				pass
			
		# Insert the new entry at the beginning of the list (for LRU).
		cache[set_index].insert(0, (page, cnt[set_index]))


		# Increment the counter for the current set.
		cnt[set_index] += 1
		counter += 1

		if counter % 100000 == 0:
			print counter

	# Done. Now write this to a file.
	outFile = open('prefetch_data.txt', 'w')
	for i in range(NUM_SETS):
		outFile.write('set '+str(i)+'\n')
		outFile.write(str(prefetch[i])+'\n\n')

process_tracefile(sys.argv[1])

