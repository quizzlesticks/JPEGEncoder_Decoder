import JPEGDecoder
import JPEGEncoder
import numpy as np
from BinaryHelpers import decToBinN

class SEG_MARKERS:
    SOI = [0xff, 0xd8, 0]             #start of image
    SOI_IND = 0
    SOF0 = [0xff, 0xc0, 1]            #start of frame baseline DCT, v
    SOF0_IND = 1
    SOF2 = [0xff, 0xc2, 1]            #start of frame progressive DCT, v
    SOF2_IND = 2
    DHT = [0xff, 0xc4, 1]             #huffman table/tables
    DHT_IND = 3
    DQT = [0xff, 0xdb, 1]             #define quant table
    DQT_IND = 4
    DRI = [0xff, 0xdd, 1]             #define restart interval, has a payload of 4 bytes, length is always 4 but can be read
    DRI_IND = 5
    SOS = [0xff, 0xda, 0]             #start of scan, marked as non variable so we dont skip scan section
    SOS_IND = 6
    JFIF_APP0 = [0xff, 0xe0, 1]       #technically always 0xff, 0xeN where APPn describes format (0=jpeg,1=Exif)
    JFIF_APP0_IND = 7
    COM = [0xff, 0xfe, 1]          #text comment
    COM_IND = 8
    EOI = [0xff, 0xd9, 0]             #end of image
    EOI_IND = 9
    SEG_NAMES = ["Start of Image", "Start of Frame (Baseline DCT)", "Start of Frame (Progressive)", "Define Huffman Table", "Define Quantization Table", "Define Restart Interval", "Start of Scan", "JFIF App Data 0", "Comment", "End of Image"]

    def __init__(self):
        self.SEGS = [self.SOI, self.SOF0, self.SOF2, self.DHT, self.DQT, self.DRI, self.SOS, self.JFIF_APP0, self.COM, self.EOI]

class JPEG:
    DIFF = JPEGDecoder.differenceWithMemoryLU()
    ZIGZAGINDICESFROM = np.argsort(JPEGDecoder.EntropyIndices().indices)
    SEGS = SEG_MARKERS()
    APP0 = -1 #Should be an APP0 Block
    QUANT_TABLE = JPEGDecoder.QUANTTABLE_BLOCK()
    HUFF_TABLE = JPEGDecoder.HUFFTABLE_BLOCK()
    SOF0 = -1
    SOSHEADER = -1
    Image = np.zeros([0], dtype=np.uint8)

    def __init__(self, filename):
        self.filename = filename

    def encode(self, outfilename):
        debug_f = open("deleteme",'w')
        debug_row = 0
        debug_col = 0
        self.decode()

        #self.Image = np.zeros((24,32),dtype=np.uint8)+255
        #drow = 1
        #dcol = 1
        #self.Image[8*drow:8*drow+8, 8*dcol:8*dcol+8] = np.zeros((8,8)) - 255

        debug_f.write("Image\n")
        debug_f.write(str(self.Image[8*debug_row:8+8*debug_row,8*debug_col:8+8*debug_col]) + "\n\n")

        shape = self.Image.shape
        height = shape[0]
        width = shape[1]
        mcu_height = height
        mcu_width = width
        if(width%8 != 0):
            mcu_width += 8-width%8
        if(height%8 != 0):
            mcu_height += 8-height%8
        if(mcu_width != width):
            self.Image = np.append(self.Image, np.zeros((mcu_width-width,height),dtype=np.uint8),axis=0)
        if(mcu_height != height):
            self.Image = np.append(self.Image, np.zeros((mcu_width,mcu_height-height),dtype=np.uint8),axis=1)
        mcu_column_count = mcu_width/8
        mcu_row_count = mcu_height/8
        self.Image = self.Image.astype(np.float) - 128

        debug_f.write("Image - 128\n")
        debug_f.write(str(self.Image[8*debug_row:8+8*debug_row,8*debug_col:8+8*debug_col]) + "\n\n")

        DIFFLD = JPEGEncoder.differenceWithMemoryLD()
        QUANT = JPEGEncoder.QUANT_BLOCK()
        ZIGZAGINDICESTO = JPEGDecoder.EntropyIndices().indices
        QUANT_TABLE = JPEGEncoder.QUANT_BLOCK().QUANT_TABLE
        RL_BYTES_DC = []
        RL_PAIRS_DC = []
        RL_BYTES_AC = []
        RL_PAIRS_AC = []
        for row in range(mcu_row_count):
            for col in range(mcu_column_count):
                self.Image[row*8:row*8+8, col*8:col*8+8] = JPEGEncoder.DCT2(self.Image[row*8:row*8+8, col*8:col*8+8])
                self.Image[row*8,col*8] = DIFFLD.diff(self.Image[row*8, col*8])
                self.Image[row*8:row*8+8, col*8:col*8+8] = np.round(np.divide(self.Image[row*8:row*8+8, col*8:col*8+8], QUANT_TABLE))
                a = np.reshape(self.Image[row*8:row*8+8, col*8:col*8+8], 64)[ZIGZAGINDICESTO].astype(np.int)
                run = 0
                size, amp = JPEGEncoder.runlengthAmplitudeLD(a[0])
                RL_PAIRS_DC.append((size,amp))
                RL_BYTES_DC.append([size])
                tmp_pairs = []
                tmp_bytes = []
                for i in range(1,63):
                    if(np.sum(np.abs(a[i:])) == 0):
                        tmp_pairs.append((0,''))
                        tmp_bytes.append(0)
                        break
                    if(a[i] != 0):
                        size, amp = JPEGEncoder.runlengthAmplitudeLD(a[i])
                        tmp_pairs.append(( (run<<4)+size ,amp))
                        tmp_bytes.append((run<<4)+size)
                        run = 0
                    else:
                        run += 1
                        if(run == 16):
                            tmp_pairs.append((15<<4,''))
                            tmp_bytes.append(15<<4)
                            run = 0
                RL_BYTES_AC.append(tmp_bytes)
                RL_PAIRS_AC.append(tmp_pairs)
        self.Image = self.Image.astype(np.int)
        debug_f.write("dct2(Image - 128)\n")
        debug_f.write(str(self.Image[8*debug_row:8+8*debug_row,8*debug_col:8+8*debug_col]) + "\n\n")
        debug_f.write("dct2(Image - 128)*Q\n")
        debug_f.write(str(np.multiply(QUANT_TABLE,self.Image[8*debug_row:8+8*debug_row,8*debug_col:8+8*debug_col])) + "\n\n")
        AC_HUFF = JPEGEncoder.PREMADE_HUFF("AC")
        DC_HUFF = JPEGEncoder.PREMADE_HUFF("DC")
        #AC_HUFF = JPEGEncoder.HUFF_BLOCK(RL_BYTES_AC)
        #DC_HUFF = JPEGEncoder.HUFF_BLOCK(RL_BYTES_DC)
        bitstream = ""
        for i in range(len(RL_BYTES_DC)):
            bitstream += DC_HUFF.lookup(RL_PAIRS_DC[i][0])
            bitstream += RL_PAIRS_DC[i][1]
            for each in RL_PAIRS_AC[i]:
                bitstream += AC_HUFF.lookup(each[0])
                bitstream += each[1]
        if(len(bitstream)%8 != 0):
            bitstream += "1"*(8-len(bitstream)%8)
        b = []
        #SOI
        b += self.SEGS.SOI[0:2]
        #APP0 Header
        app0_bytes = [0x4a,0x46,0x49,0x46,0x00,0x01,0x00,0x00,0x00,0x01,0x00,0x01,0x00,0x00]
        b += self.SEGS.JFIF_APP0[0:2]
        b.append(((len(app0_bytes)+2)>>8)&0xFF)
        b.append((len(app0_bytes)+2)&0xFF)
        b += app0_bytes
        #Quant table
        b += self.SEGS.DQT[0:2]
        b += [0x00, 0x43, 0x00]
        b += list(np.reshape(QUANT_TABLE, 64)[ZIGZAGINDICESTO])
        #DC Huffman Table
        dc_table_bytes = [0x00]
        dc_table_bytes += DC_HUFF.getTableBytes()
        b += self.SEGS.DHT[0:2]
        b.append(((len(dc_table_bytes)+2)>>8)&0xFF)
        b.append((len(dc_table_bytes)+2)&0xFF)
        b += dc_table_bytes
        #AC Huffman Table
        ac_table_bytes = [0x10]
        ac_table_bytes += AC_HUFF.getTableBytes()
        b += self.SEGS.DHT[0:2]
        b.append(((len(ac_table_bytes)+2)>>8)&0xFF)
        b.append((len(ac_table_bytes)+2)&0xFF)
        b += ac_table_bytes
        #SOF0 Block
        sof0_bytes = [0x08, (height>>8)&0xFF, height&0xFF, (width>>8)&0xFF, width&0xFF, 0x01, 0x01, 0x11, 0x00]
        b += self.SEGS.SOF0[0:2]
        b.append(((len(sof0_bytes)+2)>>8)&0xFF)
        b.append((len(sof0_bytes)+2)&0xFF)
        b += sof0_bytes
        #SOS Header
        b += self.SEGS.SOS[0:2]
        b += [0x00,0x08,0x01, 0x01, 0x00, 0x00, 63, 0x00]
        #stream bytes
        check_me = []
        for i in range(len(bitstream)/8):
            check_me.append(int(bitstream[i*8:i*8+8],2))
        check_me_arr = np.array(check_me, dtype=np.uint8)
        inds = np.where(check_me_arr == 255)[0]
        insert_inc = 1
        for i in range(len(inds)):
            check_me.insert(inds[i]+insert_inc, 0)
            insert_inc += 1
        b += check_me
        #EOI
        b += self.SEGS.EOI[0:2]
        #Write out
        f = open(outfilename, 'w')
        f.write(bytearray(b))
        f.close()

    def decode(self):
        #who needs descriptive variables :)
        a = open(self.filename, "rb")
        b = a.read()
        c = []
        for d in b:
            c.append(ord(d))
        i = 0
        #find the SOI
        while(1):
            if(c[i] == self.SEGS.SOI[0] and c[i+1] == self.SEGS.SOI[1]):
                i += 2
                break
            #If it's a comment skip over it
            if(c[i] == self.SEGS.COM[0] and c[i+1] == self.SEGS.COM[1]):
                i += 2 + (c[i+2]<<8) + c[i+2+1]
                #if we are at the end of the file after skipping
                if(i >= len(c)):
                    raise Exception("Not a JPEG.")
                continue
            i += 1
            #if we are at the end of the file after reading
            if(i == len(c)):
                raise Exception("Not a JPEG.")
        #It is a JPEG, decode it
        #find JFIF Header
        if(c[i] == self.SEGS.JFIF_APP0[0] and c[i+1] == self.SEGS.JFIF_APP0[1]):
            i += 2
            size_of_block = (c[i]<<8) + c[i+1]
            self.APP0 = JPEGDecoder.APP0_BLOCK(c[i:i+size_of_block])
            i += size_of_block
        else:
            raise Exception("No JFIF_APP0 seg immediately after SOI")
        while(1):
            break_flag = False
            for seg_ind in range(len(self.SEGS.SEGS)):
                if(c[i] == self.SEGS.SEGS[seg_ind][0] and c[i+1] == self.SEGS.SEGS[seg_ind][1]):
                    if(seg_ind == self.SEGS.EOI_IND):
                        return
                    elif(seg_ind == self.SEGS.DQT_IND):
                        i += 2
                        size_of_block = (c[i]<<8) + c[i+1]
                        self.QUANT_TABLE.newTable(c[i:i+size_of_block])
                        i += size_of_block
                    elif(seg_ind == self.SEGS.DHT_IND):
                        i += 2
                        size_of_block = (c[i]<<8) + c[i+1]
                        self.HUFF_TABLE.newTable(c[i:i+size_of_block])
                        i += size_of_block
                    elif(seg_ind == self.SEGS.SOF0_IND):
                        i += 2
                        size_of_block = (c[i]<<8) + c[i+1]
                        self.SOF0 = JPEGDecoder.SOF0_BLOCK(c[i:i+size_of_block])
                        self.Image = np.zeros((self.SOF0.mcu_height, self.SOF0.mcu_width, self.SOF0.number_of_components), dtype=np.int)
                        i += size_of_block
                    elif(seg_ind == self.SEGS.SOS_IND):
                        i += 2
                        size_of_block = (c[i]<<8) + c[i+1]
                        self.SOSHEADER = JPEGDecoder.SOSHEADER_BLOCK(c[i:i+size_of_block])
                        i += size_of_block
                        i += self.readStream(c[i:])
                        self.Image = self.Image[0:self.SOF0.image_height,0:self.SOF0.image_width,:]
                        if(self.SOF0.number_of_components == 1):
                            self.Image = np.reshape(self.Image,(self.SOF0.image_height,self.SOF0.image_width)).astype(np.uint8)
                    #if variable length, read header for skip forward amount
                    elif(self.SEGS.SEGS[seg_ind][2]):
                        i += 2 + (c[i+2]<<8) + c[i+2+1]
                    else:
                        i += 2
                    break_flag = True
                    break
            if(not break_flag):
                i += 1
                if(i == len(c)):
                    raise Exception("End of file while decoding.")

    def readStream(self, stream):
        mcu_cur_row = 0
        mcu_cur_col = 0
        mcu = np.zeros(64,dtype=np.int)
        i = 0
        num_comps = self.SOSHEADER.number_of_components
        cur_comp = 0
        cur_comp_id = self.SOSHEADER.components[cur_comp][self.SOSHEADER.COMP_ID_INDEX]
        cur_ac_table_index = self.SOSHEADER.components[cur_comp][self.SOSHEADER.AC_TABLE_INDEX]
        cur_ac_table = self.HUFF_TABLE.AC_TABLE[cur_ac_table_index]
        cur_ac_table_keys = self.HUFF_TABLE.AC_TABLE_KEYS[cur_ac_table_index]
        cur_dc_table_index = self.SOSHEADER.components[cur_comp][self.SOSHEADER.DC_TABLE_INDEX]
        cur_dc_table = self.HUFF_TABLE.DC_TABLE[cur_dc_table_index]
        cur_dc_table_keys = self.HUFF_TABLE.DC_TABLE_KEYS[cur_dc_table_index]
        cur_quant_table = self.QUANT_TABLE.TABLE[self.SOF0.components[JPEGDecoder.COMP_ID[cur_comp_id]][self.SOF0.QUANT_TABLE_NUMBER_INDEX]]
        state = "DC"
        cur_mcu_index = 0 #goes from 0 to 64
        run = -1
        length_needed = -1
        bitstream = ""
        bitdepth = 1
        total_bits_used = 0
        while(1):
            #check for markers
            if(stream[i] == 0xFF and stream[i+1] != 0x00):
                if(stream[i+1] == self.SEGS.EOI[1]):
                    return i
                else:
                    raise Exception("Found a marker midstream that isn't EOI. IDK what to do.")
            elif(stream[i] == 0xFF and stream[i+1] == 0x00):
                #if current byte is byte stuffing marker move two ahead and add 0xFF
                bitstream += decToBinN(stream[i], 8)
                i += 2
            else:
                #just add byte it's not a marker pair
                bitstream += decToBinN(stream[i], 8)
                i += 1
            #deal with current bitstream
            while(1):
                if(state == "EOB"):
                    #Dequantize
                    mcu = mcu * cur_quant_table
                    mcu = mcu[self.ZIGZAGINDICESFROM]
                    mcu[0] = self.DIFF.diff(mcu[0])
                    mcu = JPEGDecoder.IDCT2(np.reshape(mcu,(8,8)))+128
                    mcu[mcu<0] = 0
                    mcu[mcu>255] = 255
                    self.Image[mcu_cur_row*8:mcu_cur_row*8+8, mcu_cur_col*8:mcu_cur_col*8+8, cur_comp_id-1] = mcu
                    mcu_cur_col += 1
                    if(mcu_cur_col == self.SOF0.mcu_column_count):
                        mcu_cur_col = 0
                        mcu_cur_row += 1
                        if(mcu_cur_row == self.SOF0.mcu_row_count):
                            #align to byte boundary
                            if(total_bits_used%8 != 0):
                                bitstream = bitstream[8-total_bits_used%8:]
                                total_bits_used += 8-total_bits_used%8
                            return total_bits_used/8
                    mcu = np.zeros(64,dtype=np.int)
                    cur_comp += 1
                    if(cur_comp == num_comps):
                        cur_comp = 0
                    cur_comp_id = self.SOSHEADER.components[cur_comp][self.SOSHEADER.COMP_ID_INDEX]
                    cur_ac_table_index = self.SOSHEADER.components[cur_comp][self.SOSHEADER.AC_TABLE_INDEX]
                    cur_ac_table = self.HUFF_TABLE.AC_TABLE[cur_ac_table_index]
                    cur_ac_table_keys = self.HUFF_TABLE.AC_TABLE_KEYS[cur_ac_table_index]
                    cur_dc_table_index = self.SOSHEADER.components[cur_comp][self.SOSHEADER.DC_TABLE_INDEX]
                    cur_dc_table = self.HUFF_TABLE.DC_TABLE[cur_dc_table_index]
                    cur_dc_table_keys = self.HUFF_TABLE.DC_TABLE_KEYS[cur_dc_table_index]
                    cur_quant_table = self.QUANT_TABLE.TABLE[self.SOF0.components[JPEGDecoder.COMP_ID[cur_comp_id]][self.SOF0.QUANT_TABLE_NUMBER_INDEX]]
                    state = "DC"
                    cur_mcu_index = 0
                    run = -1
                    length_needed = -1
                    bitdepth = 1
                if(bitdepth > len(bitstream) or length_needed > len(bitstream)):
                    #we need another byte off the stream
                    break
                elif(state == "DC"):
                    #find DC component
                    if(bitstream[:bitdepth] not in cur_dc_table_keys[bitdepth]):
                        #key isn't in table, check next depth
                        bitdepth += 1
                    else:
                        #key is in table
                        rl_byte = cur_dc_table[bitdepth][bitstream[:bitdepth]]
                        bitstream = bitstream[bitdepth:]
                        total_bits_used += bitdepth
                        bitdepth = 1
                        if(rl_byte == 0):
                            mcu[cur_mcu_index] = 0
                            cur_mcu_index += 1
                            state = "AC"
                            continue
                        length_needed = rl_byte
                        if(length_needed > len(bitstream)):
                            state = "DC_FILL"
                            break
                        else:
                            mcu[cur_mcu_index] = JPEGDecoder.runlengthAmplitudeLU(length_needed, int(bitstream[:length_needed],2))
                            bitstream = bitstream[length_needed:]
                            cur_mcu_index += 1
                            total_bits_used += length_needed
                            length_needed = -1
                            state = "AC"
                elif(state == "DC_FILL"):
                    #we found something already but needed to fill bitstream more
                    mcu[cur_mcu_index] = JPEGDecoder.runlengthAmplitudeLU(length_needed, int(bitstream[:length_needed],2))
                    bitstream = bitstream[length_needed:]
                    cur_mcu_index += 1
                    total_bits_used += length_needed
                    length_needed = -1
                    state = "AC"
                elif(state == "AC"):
                    if(bitstream[:bitdepth] not in cur_ac_table_keys[bitdepth]):
                        #key isn't in table, check next depth
                        bitdepth += 1
                    else:
                        #key is in table
                        rl_byte = cur_ac_table[bitdepth][bitstream[:bitdepth]]
                        bitstream = bitstream[bitdepth:]
                        total_bits_used += bitdepth
                        bitdepth = 1
                        if(rl_byte == 0):
                            state = "EOB"
                            continue
                        length_needed = rl_byte & 0xF
                        run = (rl_byte & 0xF0) >> 4
                        if(length_needed > len(bitstream)):
                            state = "AC_FILL"
                            break
                        else:
                            for z in range(run):
                                mcu[cur_mcu_index] = 0
                                cur_mcu_index += 1
                                run -= 1
                            if(length_needed == 0):
                                mcu[cur_mcu_index] = 0
                            else:
                                mcu[cur_mcu_index] = JPEGDecoder.runlengthAmplitudeLU(length_needed, int(bitstream[:length_needed],2))
                            cur_mcu_index += 1
                            if(cur_mcu_index == 64):
                                state = "EOB"
                            bitstream = bitstream[length_needed:]
                            total_bits_used += length_needed
                            length_needed = -1
                elif(state == "AC_FILL"):
                    for z in range(run):
                        mcu[cur_mcu_index] = 0
                        cur_mcu_index += 1
                        run -= 1
                    mcu[cur_mcu_index] = JPEGDecoder.runlengthAmplitudeLU(length_needed, int(bitstream[:length_needed],2))
                    cur_mcu_index += 1
                    if(cur_mcu_index == 64):
                        state = "EOB"
                    else:
                        state = "AC"
                    bitstream = bitstream[length_needed:]
                    total_bits_used += length_needed
                    length_needed = -1
