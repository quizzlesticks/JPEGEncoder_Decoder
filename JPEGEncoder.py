from BinaryHelpers import decToBinN
import numpy as np

class PREMADE_HUFF:
    premade_Y_dc_counts = [0, 1, 5, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0]
    premade_Y_dc_codes = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    premade_Y_ac_counts = [0, 2, 1, 3, 3, 2, 4, 3, 5, 5, 4, 4, 0, 0, 1, 125]
    premade_Y_ac_codes = [0x01, 0x02,
                          0x03,
                          0x00, 0x04, 0x11,
                          0x05, 0x12, 0x21,
                          0x31, 0x41,
                          0x06, 0x13, 0x51, 0x61,
                          0x07, 0x22, 0x71,
                          0x14, 0x32, 0x81, 0x91, 0xA1,
                          0x08, 0x23, 0x42, 0xB1, 0xC1,
                          0x15, 0x52, 0xD1, 0xF0,
                          0x24, 0x33, 0x62, 0x72,
                          0x82,
                          0x09, 0x0a, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x25, 0x26, 0x27,
                          0x28, 0x29, 0x2A, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A,
                          0x43, 0x44, 0x45, 0x46, 0x47, 0x48, 0x49, 0x4a, 0x53, 0x54,
                          0x55, 0x56, 0x57, 0x58, 0x59, 0x5a, 0x63, 0x64, 0x65, 0x66,
                          0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75, 0x76, 0x77, 0x78,
                          0x79, 0x7A, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89, 0x8A,
                          0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9a, 0xa2,
                          0xa3, 0xa4, 0xa5, 0xa6, 0xa7, 0xa8, 0xa9, 0xaa, 0xb2, 0xb3,
                          0xb4, 0xb5, 0xb6, 0xb7, 0xb8, 0xb9, 0xba, 0xc2, 0xc3, 0xc4,
                          0xc5, 0xc6, 0xc7, 0xc8, 0xc9, 0xca, 0xd2, 0xd3, 0xd4, 0xd5,
                          0xd6, 0xd7, 0xd8, 0xd9, 0xda, 0xe1, 0xe2, 0xe3, 0xe4, 0xe5,
                          0xe6, 0xe7, 0xe8, 0xe9, 0xea, 0xf1, 0xf2, 0xf3, 0xf4, 0xf5,
                          0xf6, 0xf7, 0xf8, 0xf9, 0xfa]
    table = {}

    def __init__(self,type):
        if(type == "DC"):
            self.createHuffmanTableFromDepthCode(self.premade_Y_dc_counts, self.premade_Y_dc_codes)
        else:
            self.createHuffmanTableFromDepthCode(self.premade_Y_ac_counts, self.premade_Y_ac_codes)

    def createHuffmanTableFromDepthCode(self, depth_counts, codes):
        cur_depth = 1 #this iexes into depth_counts by cur-1, indexing into LUT is cur
        huffman_lut = {}
                           #we index the tree by depths, each depth contains a LUT
                           #the 0 depth dictionary is always empty
                           #there can be 16 possible LUTs so we just start with 17 empty dictionaries
                           #so that indexing makes sense
        if(len(codes) == 0 or sum(depth_counts) == 0):
            return huffman_lut
        #find the first nonzero bit depth
        for j in range(len(depth_counts)):
            if(depth_counts[j] == 0):
                cur_depth += 1
            else:
                break
        #to make the right oriented table that we expect start
        #at the highest depth (cur_depth) with i=0, assign this to
        #the first code, add 1 to it for the next code in the depth,
        #if the depth changes then add 1 and double (bitshift left 1)
        i = 0 #this is the current bitstream
        used_in_cur_depth = 0
        for code in codes:
            huffman_lut[code] = decToBinN(i,cur_depth)
            i += 1
            used_in_cur_depth += 1
            if(used_in_cur_depth == depth_counts[cur_depth-1]):
                i *= 2
                cur_depth += 1
                used_in_cur_depth = 0
                while(cur_depth != 17 and depth_counts[cur_depth-1] == 0):
                    cur_depth += 1
                    i *= 2
        self.table = huffman_lut

    def lookup(self,code):
        return self.table[code]

    def getTableBytes(self):
        b = []
        depths = []
        for i in range(0,17):
            depths.append([])
        for key in self.table.keys():
            depths[len(self.table[key])].append(key)
        #depths[i] = [3, 198, 20, 22, 90]
        for i in range(1,17):
            if(len(depths[i]) == 0):
                b.append(0)
                continue
            vals = np.array([int(self.table[a],2) for a in depths[i]], dtype=np.uint16)
            #vals = [4,1,5,6,0]
            inds = np.argsort(vals)
            #inds = [4,1,0,2,3]
            ordered_keys = np.array(depths[i],dtype=np.int64)[inds]
            #ordered_keys = [90, 198, 3, 20, 22]
            depths[i] = list(ordered_keys)
            b.append(len(depths[i]))
        for i in range(1,17):
            b += depths[i]
        return b

FREQ_IND = 0
BITSTRING_IND = 1
class HUFF_LEAF:
    left = -1
    right = -1
    value = -1
    freq = -1

    def __init__(self,freq_or_left,value_or_right,isvalue):
        if(isvalue):
            self.freq = freq_or_left
            self.value = value_or_right
        else:
            self.left = freq_or_left
            self.right = value_or_right
            self.freq = self.left.freq + self.right.freq

    def dive(self,bits,depth,d):
        if(self.value != -1):
            if(depth == 0):
                d[self.value] = [self.freq, '0']
                return d
            s = bin(bits)[2:]
            if(len(s) != depth):
                s = "0"*(depth-len(s)) + s
            d[self.value] = [self.freq, s]
            return d
        else:
            #When moving left mult 2 add 0
            self.left.dive(bits*2,depth+1,d)
            #When moving right mult 2 add 1
            self.right.dive(bits*2+1, depth+1, d)
            return d

class HUFF_BLOCK:
    top_leaf = -1
    table = -1

    def __init__(self,v):
        runlengths = []
        self.table = {}
        for each in v:
            for i in range(len(each)):
                runlengths.append(each[i])
        unique, counts = np.unique(runlengths, return_counts=True)
        if(len(counts) == 1):
            self.top_leaf = HUFF_LEAF(counts[0],unique[0],True)
            self.top_leaf.dive(0,0,self.table)
            return
        sort_inds = np.argsort(counts)
        unique = list(unique[sort_inds])
        counts = list(counts[sort_inds])
        while(1):
            if(type(unique[0]) == np.int64):
                left_leaf = HUFF_LEAF(counts.pop(0), unique.pop(0), True)
            else:
                left_leaf = unique.pop(0)
                counts.pop(0)
            if(type(unique[0]) == np.int64):
                right_leaf = HUFF_LEAF(counts.pop(0), unique.pop(0), True)
            else:
                right_leaf = unique.pop(0)
                counts.pop(0)
            new_leaf = HUFF_LEAF(left_leaf, right_leaf, False)
            if(counts == []):
                break
            for i in range(len(counts)):
                if(new_leaf.freq < counts[i]):
                    counts.insert(i, new_leaf.freq)
                    unique.insert(i, new_leaf)
                    break
                if(i == len(counts)-1):
                    #append
                    counts.append(new_leaf.freq)
                    unique.append(new_leaf)
        self.top_leaf = new_leaf
        self.top_leaf.dive(0,0,self.table)
        self.leftOrientTable()

    def leftOrientTable(self):
        depths = []
        for i in range(0,17):
            depths.append([])
        for key in self.table.keys():
            depths[len(self.table[key][BITSTRING_IND])].append(key)
        min_depth = 1
        for i in range(1,17):
            if(len(depths[i]) != 0):
                min_depth = i
                break
        val = 0
        for i in range(min_depth,17):
            if(len(depths[i]) == 0):
                val *= 2
                continue
            for key in depths[i]:
                s = bin(val)[2:]
                if(len(s) != i):
                    s = "0"*(i-len(s)) + s
                self.table[key][BITSTRING_IND] = s
                val += 1
            val *= 2

    def lookup(self, val):
        return self.table[val][BITSTRING_IND]

    def getTableBytes(self):
        b = []
        depths = []
        for i in range(0,17):
            depths.append([])
        for key in self.table.keys():
            depths[len(self.table[key][BITSTRING_IND])].append(key)
        #depths[i] = [3, 198, 20, 22, 90]
        for i in range(1,17):
            if(len(depths[i]) == 0):
                b.append(0)
                continue
            vals = np.array([int(self.table[a][BITSTRING_IND],2) for a in depths[i]], dtype=np.uint16)
            #vals = [4,1,5,6,0]
            inds = np.argsort(vals)
            #inds = [4,1,0,2,3]
            ordered_keys = np.array(depths[i],dtype=np.int64)[inds]
            #ordered_keys = [90, 198, 3, 20, 22]
            depths[i] = list(ordered_keys)
            b.append(len(depths[i]))
        for i in range(1,17):
            b += depths[i]
        return b


class EntropyIndices:
    def __init__(self):
        self.indices = np.array((),dtype=np.int)
        row = 0
        col = 0
        state = "zig"
        while(1):
            self.indices = np.append(self.indices,row*8+col)
            if(row == 7 and col == 7):
                break
            if(state == "zig" and col == 7):
                state = "zag"
                row += 1
            elif(state == "zig" and row == 0):
                state = "zag"
                col += 1
            elif(state == "zag" and row == 7):
                state = "zig"
                col += 1
            elif(state == "zag" and col == 0):
                state = "zig"
                row += 1
            elif(state == "zig"):
                row -= 1
                col += 1
            elif(state == "zag"):
                row += 1
                col -= 1

class QUANT_BLOCK:
    QUANT_TABLE = -1
    def __init__(self):
        self.QUANT_TABLE = np.array([4,6,5,8,12,20,26,31,6,6,7,10,13,29,30,28,7,7,8,12,20,29,35,28,7,9,11,15,26,44,40,31,9,11,19,28,32,41,52,57,46,25,32,39,44,52,57,46,25,32,39,44,52,61,60,51,36,46,48,49,56,50,52,50])
        self.QUANT_TABLE = np.reshape(self.QUANT_TABLE,(8,8))

class differenceWithMemoryLD:
    last = 0

    def diff(self,cur):
        out = cur-self.last
        self.last = cur
        return out

SQUARES = [2**a for a in range(12)]
def runlengthAmplitudeLD(amp):
    if(amp == 0):
        return 0,''
    if(amp < 0):
        b = bin(-amp)[2:].replace('1','2').replace('0','1').replace('2','0')
        l = len(b)
        return l,b
    else:
        b = bin(amp)[2:]
        l = len(b)
        return l,b

DCT_X, DCT_V = np.meshgrid(np.linspace(0,7,8),np.linspace(0,7,8))
DCT_C = np.cos(np.pi*np.multiply(2.*DCT_X+1, DCT_V)/16.)
DCT_A = np.array((np.sqrt(1/8.)))
for idct_i in range(7):
    DCT_A = np.append(DCT_A, np.sqrt(2/8.))
def DCT(I):
    return np.multiply(DCT_A,DCT_C.dot(I))

def DCT2(I):
    #IDCT the rows
    out = np.zeros((8,8))
    for i in range(8):
        out[i] = DCT(I[i])
    for i in range(8):
        out[:,i] = DCT(out[:,i])
    return np.round(out)
