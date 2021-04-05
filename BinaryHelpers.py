def decToBinN(d, N):
    b = bin(d).replace("0b", "")
    b = "0"*(N-len(b)) + b
    return b
