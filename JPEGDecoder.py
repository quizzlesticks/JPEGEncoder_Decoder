from BinaryHelpers import decToBinN
from textwrap import wrap
import numpy as np

class EntropyIndices:
    def __init__(self):
        self.indices = []
        row = 0
        col = 0
        state = "zig"
        while(1):
            self.indices.append(row*8+col)
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

class SEG_MARKERS:
    SOI = [0xff, 0xd8, 0]             #start of image
    SOI_i = 0
    SOF0 = [0xff, 0xc0, 1]            #start of frame baseline DCT, v
    SOF0_i = 1
    SOF2 = [0xff, 0xc2, 1]            #start of frame progressive DCT, v
    SOF2_i = 2
    DHT = [0xff, 0xc4, 1]             #huffman table/tables
    DHT_i = 3
    DQT = [0xff, 0xdb, 1]             #define quant table
    DQT_i = 4
    DRI = [0xff, 0xdd, 1]             #define restart interval, has a payload of 4 bytes, length is always 4 but can be read
    DRI_i = 5
    SOS = [0xff, 0xda, 0]             #start of scan, marked as non variable so we dont skip scan section
    SOS_i = 6
    JFIF_APP0 = [0xff, 0xe0, 1]       #technically always 0xff, 0xeN where APPn describes format (0=jpeg,1=Exif)
    JFIF_APP0_i = 7
    COM = [0xff, 0xfe, 1]          #text comment
    COM_i = 8
    EOI = [0xff, 0xd9, 0]             #end of image
    EOI_i = 9
    SEG_NAMES = ["Start of Image", "Start of Frame (Baseline DCT)", "Start of Frame (Progressive)", "Define Huffman Table", "Define Quantization Table", "Define Restart Interval", "Start of Scan", "JFIF App Data 0", "Comment", "End of Image"]

    def __init__(self):
        self.SEGS = [self.SOI, self.SOF0, self.SOF2, self.DHT, self.DQT, self.DRI, self.SOS, self.JFIF_APP0, self.COM, self.EOI]

GOOD = True
BAD = False

class APP0_BLOCK:
    identifier = ""
    version = ""
    density_units = ""
    x_density = -1
    y_density = -1
    thumbnail_width = -1
    thumbnail_height = -1
    parse_state = BAD

    def __init__(self, block):
        i = 0
        leng = (block[i]<<8) + block[i+1]
        i += 2
        end_i = i+1
        while(1):
            if(block[end_i] == 0x00):
                break
            end_i += 1
            if(end_i == len(block)):
                raise Exception("No NULL char termination for Identifier in APP0 header.")
        for letter in block[i:end_i]:
            self.identifier += chr(letter)
        i += end_i-i+1
        self.version = str(block[i]) + "." + str(block[i+1])
        i += 2
        if(block[i] == 0):
            self.density_units = "None"
        elif(block[i] == 1):
            self.density_units = "PPI"
        elif(block[i] == 2):
            self.density_units = "PPCM"
        else:
            raise Exception("Undefined density unit in APP0 header.")
        i += 1
        self.x_density = (block[i]<<8) + block[i+1]
        if(self.x_density == 0):
            raise Exception("XDensity was read as 0 in APP0 header. XDensity cannot be 0.")
        i += 2
        self.y_density = (block[i]<<8) + block[i+1]
        if(self.y_density == 0):
            raise Exception("YDensity was read as 0 in APP0 header. YDensity cannot be 0.")
        i += 2
        self.thumbnail_width = block[i]
        i += 1
        self.thumbnail_height = block[i]
        #I don't bother with thumbnails
        i += 1 + 3*self.thumbnail_height*self.thumbnail_width
        if(i == leng):
            self.parse_state = GOOD
        else:
            self.parse_state = BAD

class QUANTTABLE_BLOCK:
    #The quant tables are stored in the zig zag order but this doesn't
    #have to be undone till after the IDCT and Dequant step since
    #the streams are stored in entropy coding as well
    TABLE = []
    precision = [] #I make this  a vector incase we have two different DQT SEGS
                   #with different precisions. I don't think this can happen or
                   #is supported but whatever
    parse_state = BAD

    def newTable(self, block):
        i = 0
        leng = (block[i]<<8) + block[i]
        i += 2
        num_tables_in_block = (block[i] & 0xF) + 1
        precision_nibble = (block[i] & 0xF0) >> 4
        i += 1
        #read out tables as vectors
        for j in range(num_tables_in_block):
            if(precision_nibble == 0):
                self.precision.append(8)
                self.TABLE.append(np.array(block[i:i+64],dtype=np.uint8))
                i += 64
            else:
                self.precision.append(16)
                self.TABLE.append(np.array(block[i:i+64*2],dtype=np.uint16))
                i += 64*2
        if(i == leng):
            self.parse_state = GOOD
        else:
            self.parse_state = BAD

    def printBlock(self):
        zind = EntropyIndices().indices
        print("Quantization Table Block")
        for i in range(len(self.TABLE)):
            print("\tQuantization Table #" + str(i))
            print("\t\tPrecision (bits): " + str(self.precision[i]))
            if(self.precision[i] == 8):
                line = "\t\t" + "+-----"*8 + "+"
            else:
                line = "\t\t" + "+-------"*8 + "+"
            if(self.precision[i] == 8):
                unzigzagged_qtable = np.zeros(64,dtype=np.uint8)
            else:
                unzigzagged_qtable = np.zeros(64,dtype=np.uint16)
            unzigzagged_qtable[zind] = self.TABLE[i]
            zz = 0
            for k in range(8):
                print(line)
                colm = "\t\t"
                for m in range(8):
                    if(self.precision[i] == 8):
                        if(unzigzagged_qtable[zz] >= 100):
                            colm += "| " + str(unzigzagged_qtable[zz]) + " "
                        elif(unzigzagged_qtable[zz] >= 10):
                            colm += "|  " + str(unzigzagged_qtable[zz]) + " "
                        else:
                            colm += "|  " + str(unzigzagged_qtable[zz]) + "  "
                    else:
                        if(unzigzagged_qtable[zz] >= 10000):
                            colm += "| " + str(unzigzagged_qtable[zz]) + " "
                        elif(unzigzagged_qtable[zz] >= 1000):
                            colm += "|  " + str(unzigzagged_qtable[zz]) + " "
                        elif(unzigzagged_qtable[zz] >= 100):
                            colm += "|  " + str(unzigzagged_qtable[zz]) + "  "
                        elif(unzigzagged_qtable[zz] >= 10):
                            colm += "|   " + str(unzigzagged_qtable[zz]) + "  "
                        else:
                            colm += "|   " + str(unzigzagged_qtable[zz]) + "   "
                    zz += 1
                colm += "|"
                print(colm)
            print(line)

DC = 0
AC = 1
class HUFFTABLE_BLOCK:
    DC_TABLE = []
    DC_TABLE_KEYS = []
    AC_TABLE = []
    AC_TABLE_KEYS = []
    parse_state = BAD

    def newTable(self, block):
        i = 0
        leng = (block[i]<<8) + block[i+1]
        i += 2
        #ieterminate amount of DHT sections in block
        while(1):
            num_of_tables = (block[i] & 0xF)
            if(num_of_tables > 3):
                raise Exception("DHT is saying there is more than 3 huffman tables in block.")
            #Add one because 0 tables means 1 table
            num_of_tables += 1
            table_type = (block[i] & 0x10) >> 4
            must_be_zero = (block[i] & 0xE0)
            if(must_be_zero != 0):
                raise Exception("Must be zero bits ([7:5] of HT Info) are not zero.")
            i += 1
            for j in range(num_of_tables):
                depth_counts = block[i:i+16]
                i += 16
                N = sum(depth_counts)
                codes = block[i:i+N]
                i += N
                if(table_type == DC):
                    self.DC_TABLE.append(self.createHuffmanTableFromDepthCode(depth_counts, codes))
                    keys = []
                    for k in range(17):
                        keys.append(self.DC_TABLE[-1][k].keys())
                    self.DC_TABLE_KEYS.append(keys)
                else:
                    self.AC_TABLE.append(self.createHuffmanTableFromDepthCode(depth_counts, codes))
                    keys = []
                    for k in range(17):
                        keys.append(self.AC_TABLE[-1][k].keys())
                    self.AC_TABLE_KEYS.append(keys)
            #if this isn't true assume there is another HT definition in the block
            if(i == leng):
                break
        self.parse_state = GOOD

    def createHuffmanTableFromDepthCode(self, depth_counts, codes):
        cur_depth = 1 #this iexes into depth_counts by cur-1, indexing into LUT is cur
        huffman_lut = [{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}]
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
            huffman_lut[cur_depth][decToBinN(i,cur_depth)] = code
            i += 1
            used_in_cur_depth += 1
            if(used_in_cur_depth == depth_counts[cur_depth-1]):
                i *= 2
                cur_depth += 1
                used_in_cur_depth = 0
                while(cur_depth != 17 and depth_counts[cur_depth-1] == 0):
                    cur_depth += 1
                    i *= 2
        return huffman_lut

    def printBlock(self):
        self.printHuffmanDCTables()
        self.printHuffmanACTables()

    def printHuffmanDCTables(self):
        for table_ind in range(len(self.DC_TABLE)):
            print("DC Huffman Table (" + str(table_ind) + ")")
            #find highest bit depth for pretty printing
            highest = 0
            for i in range(17):
                if(len(self.DC_TABLE[table_ind][i].keys())):
                    highest = i
            if(highest <= 3):
                highest = 3
            row_str = "\t+---------+" + "-"*(highest+highest/4) + "+----+"
            print(row_str)
            length_bits = highest + highest/4 - 4
            if(length_bits%2==0):
                bit_left = " "*(length_bits/2)
                bit_right = bit_left
            else:
                bit_left = " "*( (length_bits-1)/2 )
                bit_right = " "*( (length_bits+1)/2 )
            length_bits += 4
            print("\t| Length  |" + bit_left + "Bits" + bit_right + "|Code|")
            for i in range(17):
                keys = self.DC_TABLE[table_ind][i].keys()
                if(len(keys)):
                    print(row_str)
                    first_key = True
                    for key in keys:
                        code = self.DC_TABLE[table_ind][i][key]
                        bits = " ".join(wrap(key, 4))
                        code_str = hex(code)
                        if(len(code_str) == 3):
                            code_str = code_str[0:2] + "0" + code_str[2]
                        if(first_key):
                            first_key = False
                            if(i >= 10):
                                print("\t| " + str(i) + " bits |" + bits + " "*(length_bits-len(bits)) + "|" + code_str + "|")
                            else:
                                print("\t|  " + str(i) + " bits |" + bits + " "*(length_bits-len(bits)) + "|" + code_str + "|")
                        else:
                            if(i >= 10):
                                print("\t|         |" + bits + " "*(length_bits-len(bits)) + "|" + code_str + "|")
                            else:
                                print("\t|         |" + bits + " "*(length_bits-len(bits)) + "|" + code_str + "|")
            print(row_str)

    def printHuffmanACTables(self):
        for table_ind in range(len(self.AC_TABLE)):
            print("AC Huffman Table (" + str(table_ind) + ")")
            #find highest bit depth for pretty printing
            highest = 0
            for i in range(17):
                if(len(self.AC_TABLE[table_ind][i].keys())):
                    highest = i
            if(highest <= 3):
                highest = 3
            row_str = "\t+---------+" + "-"*(highest+highest/4) + "+----+"
            print(row_str)
            length_bits = highest + highest/4 - 4
            if(length_bits%2==0):
                bit_left = " "*(length_bits/2)
                bit_right = bit_left
            else:
                bit_left = " "*( (length_bits-1)/2 )
                bit_right = " "*( (length_bits+1)/2 )
            length_bits += 4
            print("\t| Length  |" + bit_left + "Bits" + bit_right + "|Code|")
            for i in range(17):
                keys = self.AC_TABLE[table_ind][i].keys()
                if(len(keys)):
                    print(row_str)
                    first_key = True
                    for key in keys:
                        code = self.AC_TABLE[table_ind][i][key]
                        bits = " ".join(wrap(key, 4))
                        code_str = hex(code)
                        if(len(code_str) == 3):
                            code_str = code_str[0:2] + "0" + code_str[2]
                        if(first_key):
                            first_key = False
                            if(i >= 10):
                                print("\t| " + str(i) + " bits |" + bits + " "*(length_bits-len(bits)) + "|" + code_str + "|")
                            else:
                                print("\t|  " + str(i) + " bits |" + bits + " "*(length_bits-len(bits)) + "|" + code_str + "|")
                        else:
                            if(i >= 10):
                                print("\t|         |" + bits + " "*(length_bits-len(bits)) + "|" + code_str + "|")
                            else:
                                print("\t|         |" + bits + " "*(length_bits-len(bits)) + "|" + code_str + "|")
            print(row_str)

COMP_ID = ["UNKNOWN", "Y", "Cb", "Cr", "I", "Q"]
class SOF0_BLOCK:
    VERT_SAMP_FACTOR_INDEX = 0
    HOR_SAMP_FACTOR_INDEX = 1
    QUANT_TABLE_NUMBER_INDEX = 2
    precision = -1
    image_height = -1
    image_width = -1
    mcu_row_count = -1
    mcu_column_count = -1
    mcu_height = -1
    mcu_width = -1
    number_of_components = -1
    components = {}

    def __init__(self, block):
        i = 0
        leng = (block[i]<<8) + block[i+1]
        i += 2
        self.precision = block[i]
        i += 1
        if(self.precision != 8):
            raise Exception("SOF0 Precision is not 8. This codec only supports 8 bits per sample.")
        self.image_height = (block[i]<<8) + block[i+1]
        i += 2
        self.image_width = (block[i]<<8) + block[i+1]
        i += 2
        if(self.image_height == 0):
            raise Exception("Image height was read as 0. It cannot be 0.")
        if(self.image_width == 0):
            raise Exception("Image width was read as 0. It cannot be 0.")
        self.mcu_row_count = self.image_height/8
        if(self.image_height%8 != 0):
            self.mcu_row_count += 1
        self.mcu_column_count = self.image_width/8
        if(self.image_width%8 != 0):
            self.mcu_column_count += 1
        self.mcu_height = self.mcu_row_count * 8
        self.mcu_width = self.mcu_column_count * 8
        self.number_of_components = block[i]
        i += 1
        for j in range(self.number_of_components):
            comp_id = block[i]
            i += 1
            sample_factor_vert = block[i] & 0xF
            sample_factor_hor = (block[i] & 0xF0) >> 4
            i += 1
            quant_table_number = block[i]
            i += 1
            self.components[COMP_ID[comp_id]] = [sample_factor_vert, sample_factor_hor, quant_table_number]

    def printBlock(self):
        print("SOF0 Block")
        print("\tPrecision (bits/sample): " + str(self.precision))
        print("\tImage Dimensions (WxH): " + str(self.image_width) + "x" + str(self.image_height))
        print("\tNumber of Components: " + str(self.number_of_components))
        for key in self.components.keys():
            print("\tComponent " + str(key))
            print("\t\tSampling Factor Vertical: " + str(self.components[key][0]))
            print("\t\tSampling Factor Horizontal: " + str(self.components[key][1]))
            print("\t\tQuantization Table Index: " + str(self.components[key][2]))

class SOSHEADER_BLOCK:
    COMP_ID_INDEX = 0
    AC_TABLE_INDEX = 1
    DC_TABLE_INDEX = 2

    number_of_components = -1
    components = []

    def __init__(self, block):
        i = 0
        leng = (block[i]<<8) + block[i+1]
        i += 2
        self.number_of_components = block[i]
        i += 1
        if(self.number_of_components < 1 or self.number_of_components > 4):
            raise Exception("Number of components in scan is < 1 or > 4.")
        for j in range(self.number_of_components):
            comp_id = block[i]
            i += 1
            huffman_table_ac = block[i] & 0xF
            huffman_table_dc = (block[i] & 0xF0) >> 4
            self.components.append([comp_id, huffman_table_ac, huffman_table_dc])
            i += 1

    def printBlock(self):
        print("SOS Block Header")
        print("\tNumber of Components: " + str(len(self.components)))
        for i in range(len(self.components)):
            print("\tComponent #" + str(i))
            print("\t\tComp ID: " + COMP_ID[self.components[i][self.COMP_ID_INDEX]])
            print("\t\tAC Huffman Table Index: " + str(self.components[i][self.AC_TABLE_INDEX]))
            print("\t\tDC Huffman Table Index: " + str(self.components[i][self.DC_TABLE_INDEX]))

SQUARES = [2**a for a in range(12)]
def runlengthAmplitudeLU(bitdepth, amp):
    if(bitdepth == 0):
        return 0
    if(amp > SQUARES[bitdepth]-1):
        raise ValueError("Runlength Amplitude is greater than 2^bitdepth-1")
    elif(amp < 0):
        raise ValueError("Runlength Amplitude lookup for Amplitude < 0")
    elif(bitdepth > 11):
        raise ValueError("Runlength Amplitude lookup for Bitdepth > 11")
    if(amp & SQUARES[bitdepth-1] == 0):
        return 1-SQUARES[bitdepth]+amp
    else:
        return amp
