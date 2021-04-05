class SEG_MARKERS():
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
	COM = [0xff, 0xfe, 1]		  #text comment
	COM_IND = 8
	EOI = [0xff, 0xd9, 0]             #end of image
	EOI_IND = 9
	SEG_NAMES = ["Start of Image", "Start of Frame (Baseline DCT)", "Start of Frame (Progressive)", "Define Huffman Table", "Define Quantization Table", "Define Restart Interval", "Start of Scan", "JFIF App Data 0", "Comment", "End of Image"]

	def __init__(self):
		self.SEGS = [self.SOI, self.SOF0, self.SOF2, self.DHT, self.DQT, self.DRI, self.SOS, self.JFIF_APP0, self.COM, self.EOI]

class JPEGExaminer:
	segs = SEG_MARKERS()
	comp_id = ["UNKNOWN", "Y", "Cb", "Cr", "I", "Q"]
	i = 0

	def __init__(self, filename, print_jfif_info=True, print_quant_table=True, print_huff_table=True, print_sof0_info=True, print_sos=True):
		self.filename = filename
		self.PRINT_JFIF_APP_INFO = print_jfif_info
		self.PRINT_QUANT_TABLE = print_quant_table
		self.PRINT_HUFF_TABLE = print_huff_table
		self.PRINT_SOF0_INFO = print_sof0_info
		self.PRINT_SOS = print_sos
		a = open(filename, "rb")
		b = a.read()
		c = []
		for d in b:
			c.append(ord(d))
		self.bytes = c
		self.zind = []
		row = 0
		col = 0
		state = "zig"
		while(1):
			self.zind.append(row*8+col)
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

	def examine(self):
		#find SOI
		self.i = 0
		c = self.bytes
		while(1):
			if(c[self.i] == self.segs.SOI[0] and c[self.i+1] == self.segs.SOI[1]):
				print("Found segment at byte " + str(self.i) + ": Start of Image")
				self.i += 2
				break
			if(c[self.i] == self.segs.COM[0] and c[self.i+1] == self.segs.COM[1]):
				print("Found segment at byte " + str(self.i) + ": Comment")
				self.i += 2 + (c[self.i+2]<<8) + c[self.i+2+1]
				if(self.i >= len(c)):
					print("Not a JPEG V2")
					exit()
				continue
			self.i += 1
			if(self.i == len(c)):
				print("Not a JPEG")
				exit()
		#find JFIF Header
		if(c[self.i] == self.segs.JFIF_APP0[0] and c[self.i+1] == self.segs.JFIF_APP0[1]):
			print("Found segment at byte " + str(self.i) + ": APP0 (JFIF)")
			self.i += 2
			if(self.PRINT_JFIF_APP_INFO):
				self.print_JFIFAPP_INFO()
			size = (c[self.i]<<8)+c[self.i+1]
			self.i += size
		else:
			print("ERROR: No JFIF_APP0 seg after SOI")
			exit()
		if(c[self.i] == self.segs.JFIF_APP0[0] and c[self.i+1] == self.segs.JFIF_APP0[1]):
			print("Found segment at byte " + str(self.i) + ": APP0 (JFIF extension)")
			self.i += 2
			#skip thumbnail
			self.i += (c[self.i]<<8) + c[self.i+1]
		while(1):
			break_flag = False
			for seg_ind in range(len(self.segs.SEGS)):
				if(c[self.i] == self.segs.SEGS[seg_ind][0] and c[self.i+1] == self.segs.SEGS[seg_ind][1]):
					print("Found segment at byte " + str(self.i) + ": " + self.segs.SEG_NAMES[seg_ind])
					if(seg_ind == self.segs.EOI_IND):
						exit()
					elif(seg_ind == self.segs.DQT_IND and self.PRINT_QUANT_TABLE):
						self.print_QUANT_TABLE()
					elif(seg_ind == self.segs.DHT_IND and self.PRINT_HUFF_TABLE):
						self.print_HUFF_TABLE()
					elif(seg_ind == self.segs.SOF0_IND and self.PRINT_SOF0_INFO):
						self.print_SOF0_INFO()
					elif(seg_ind == self.segs.SOS_IND and self.PRINT_SOS):
						self.print_SOS()
					#if variable length, skip forward that much
					if(self.segs.SEGS[seg_ind][2]):
						self.i += 2 + (c[self.i+2]<<8) + c[self.i+2+1]
					else:
						self.i += 2
					break_flag = True
					break
			if(not break_flag):
				self.i += 1
				if(self.i == len(c)):
					print("End of file while decoding")
					exit()

	def print_SOS(self):
		i = self.i+2
		c = self.bytes
		leng = (c[i]<<8) + c[i+1]
		i += 2
		print("\tLength of SOS Block0 header: " + str(leng))
		num_comps = c[i]
		i += 1
		if(num_comps < 1 or num_comps > 4):
			print("ERROR: Num components is outside of [1,4] (value = " + str(num_comps) + ")")
			exit()
		print("\tNumber of components: " + str(num_comps))
		for j in range(num_comps):
			if(c[i] == 0 or c[i] > 5):
				print("\t\tComponent: " + self.comp_id[0] + " (value = " + str(c[i]) + ")")
			else:
				print("\t\tComponent: " + self.comp_id[c[i]])
			i += 1
			AC = (0x0F & c[i]) + 1
			DC = ((0xF0 & c[i])>>4) + 1
			i += 1
			if(AC-1 > 3):
				print("ERROR: Bad Huffman Table value for AC")
			if(DC-1 > 3):
				print("ERROR: Bad Huffman Table value for DC")
			print("\t\tAC Table Index: " + str(AC))
			print("\t\tDC Table Index: " + str(DC))
			#ignore 3 bytes
			i += 3
			print("\t8 Bytes starting for " + str(i))
			lt = []
			for j in range(8):
				lt.append(hex(c[i]))
				i += 1
			print("\t" + str(lt))

	def print_SOF0_INFO(self):
		i = self.i+2
		c = self.bytes
		leng = (c[i]<<8) + c[i+1]
		i += 2
		precision = c[i]
		i += 1
		height = (c[i]<<8) + c[i+1]
		i += 2
		width = (c[i]<<8) + c[i+1]
		i += 2
		num_comps = c[i]
		i += 1
		if(height == 0):
			print("ERROR: Image height is 0")
			exit()
		if(width == 0):
			print("ERROR: Image width is 0")
			exit()
		print("\tFrame Header length: " + str(leng))
		print("\tPrecision: " + str(precision))
		print("\tDimensions (WxH): " + str(width) + "x" + str(height))
		print("\tNumber of Components: " + str(num_comps))
		for j in range(num_comps):
			print("\tComponent Number " + str(i+1))
			if(c[i] == 0 or c[i] > 5):
				print("\t\tComponent: " + self.comp_id[0] + " (value = " + str(c[i]) + ")")
			else:
				print("\t\tComponent: " + self.comp_id[c[i]])
			i += 1
			sample_factor = c[i]
			vert = 0x0F & c[i]
			hor = (0xF0 & c[i])>>4
			i += 1
			print("\t\tSample Factor (Vert):(Horizontal): " + str(vert) + ":" + str(hor))
			print("\t\tQuantization Table Index: " + str(c[i]))
			i += 1
		if(i-leng == self.i+2):
			print("\tLength is in accordance with end of SOF0 data")
		else:
			print("\tERROR: Length is not in accordance with end of SOF0 data")


	def print_HUFF_TABLE(self):
		i = self.i+2
		c = self.bytes
		leng = (c[i]<<8) + c[i+1]
		i += 2
		ht_info = c[i]
		i += 1
		num_tables = (0x0F & ht_info) + 1
		ht_type = (0x10 & ht_info)>>4
		must_be_zero = (0xE0 & ht_info)>>5
		if(num_tables > 4):
			print("ERROR: Cannot have more than 4 huffman tables")
			exit()
		if(must_be_zero):
			print("ERROR: Must_be_zero in huffman table info is not zero")
			exit()
		print("\tHuffman Table Length (bytes): " + str(leng))
		if(ht_type == 0):
			print("\tHuffman Table Type: DC")
		else:
			print("\tHuffman Table Type: AC")
		num_symbols_of_length = [] #the value at ind is the number of symbols with code length=ind+1
		for j in range(16):
			num_symbols_of_length.append(c[i])
			i += 1
		number_of_codes = sum(num_symbols_of_length)
		if(number_of_codes > 256):
			print("ERROR: Number of huffman table codes is > 256")
			exit()
		for j in range(16):
			ht_str = "\t\t"
			k = j+1
			if(k >= 10):
				if(num_symbols_of_length[j] >= 100):
					ht_str += "Codes of length " + str(k) + " bits (" + str(num_symbols_of_length[j]) + " total):"
				elif(num_symbols_of_length[j] >= 10):
					ht_str += "Codes of length " + str(k) + " bits (0" + str(num_symbols_of_length[j]) + " total):"
				else:
					ht_str += "Codes of length " + str(k) + " bits (00" + str(num_symbols_of_length[j]) + " total):"
			else:
				if(num_symbols_of_length[j] >= 100):
					ht_str += "Codes of length 0" + str(k) + " bits (" + str(num_symbols_of_length[j]) + " total):"
				elif(num_symbols_of_length[j] >= 10):
					ht_str += "Codes of length 0" + str(k) + " bits (0" + str(num_symbols_of_length[j]) + " total):"
				else:
					ht_str += "Codes of length 0" + str(k) + " bits (00" + str(num_symbols_of_length[j]) + " total):"
			for k in range(num_symbols_of_length[j]):
				if(c[i] < 16):
					ht_str += " 0" + hex(c[i])[2:]
				else:
					ht_str += " " + hex(c[i])[2:]
				i += 1
			print(ht_str)
		print("\tTotal number of codes: " + str(number_of_codes))
		if(i-leng == self.i+2):
			print("\tLength is in accordance with end of Huffman Table data")
		else:
			print("\tERROR: Length is not in accordance with end of Huffman Table data")

	def print_QUANT_TABLE(self):
		i = self.i+2
		c = self.bytes
		leng = (c[i]<<8) + c[i+1]
		i += 2
		qt_info = c[i]
		i += 1
		num_tables = (qt_info & 0x0F) + 1
		precision = (qt_info & 0xF0)>>4
		num_bits = 8
		if(num_tables > 4):
			print("\tERROR: Cannot have more than 4 quantization tables")
		if(precision != 0):
			num_bits = 16
		if(3 + num_tables*(num_bits/8)*64 != leng):
			print("\tERROR: Quantization table length doesn't match given number_tables*num_bits")
		print("\tQuantization Table Length (bytes): " + str(leng))
		print("\tNumber of Tables: " + str(num_tables))
		print("\tPrecision (bits): " + str(num_bits))
		if(num_bits == 8):
			line = "\t\t" + "+-----"*8 + "+"
		else:
			line = "\t\t" + "+-------"*8 + "+"
		for j in range(num_tables):
			unzigzagged_qtable = [0] * 64
			for zz in range(64):
				if(num_bits == 8):
					unzigzagged_qtable[self.zind[zz]] = c[i]
					i += 1
				else:
					unzigzagged_qtable[self.zind[zz]] = (c[i]<<8) + c[i]
					i += 2
			print("\tQuantization Table " + str(j))
			zz = 0
			for k in range(8):
				print(line)
				colm = "\t\t"
				for m in range(8):
					if(num_bits == 8):
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
		if(i-leng == self.i+2):
			print("\tLength is in accordance with end of Quantization Table data")
		else:
			print("\tERROR: Length is not in accordance with end of Quantization Table data")

	def print_JFIFAPP_INFO(self):
		ind = self.i
		c = self.bytes
		leng = (c[ind]<<8) + c[ind+1]
		ind += 2
		print("\tLength (bytes): " + str(leng))
		end_ind = ind+1
		while(1):
			if(c[end_ind] == 0x00):
				break
			end_ind += 1
			if(end_ind == len(c)):
				print("No NULL char termination for Indentifier in APPn info")
				exit()
		idntf = ""
		for letter in c[ind:end_ind]:
			idntf += chr(letter)
		print("\tJFIF Identifier: " + idntf)
		ind += end_ind-ind+1
		print("\tVersion: " + str(c[ind]) + "." + str(c[ind+1]))
		ind += 2
		if(c[ind] == 0):
			print("\tDensity Units: No units")
		elif(c[ind] == 1):
			print("\tDensity Units: Pixels per Inch")
		elif(c[ind] == 2):
			print("\tDensity Units: Pixels per cm")
		else:
			print("\tDensity Units: ERROR")
		ind += 1
		if(c[ind] + c[ind+1] == 0):
			print("\tError: XDensity cannot be 0")
		print("\tXdensity: " + str((c[ind]<<8) + c[ind+1]))
		ind += 2
		if(c[ind] + c[ind+1] == 0):
			print("\tError: YDensity cannot be 0")
		print("\tYdensity: " + str((c[ind]<<8) + c[ind+1]))
		ind += 2
		print("\tThumbnail Width: " + str(c[ind]))
		ind += 1
		print("\tThumbnail Height: " + str(c[ind]))
		ind += 1 + 3*c[ind-1]*c[ind]
		if(ind-self.i == leng):
			print("\tLength is in accordance to end of APP0 data")
		else:
			print("\tERROR: Length is not in accordance to end of APP0 data")
