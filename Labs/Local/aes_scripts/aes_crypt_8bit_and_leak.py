import numpy as np
from aes_scripts.aes_sbox import aes_sbox
from aes_scripts.aes_mix_columns_8bit_and_leak import aes_mix_columns_8bit_and_leak
from aes_scripts.aes_shift_rows import aes_shift_rows
from aes_scripts.aes_add_round_key import aes_add_round_key
from aes_scripts.aes_round_key import aes_round_key

# function [result state rkeys mixcolumn_leak]= aes_crypt_8bit_and_leak(input_data, secret_key, encrypt)

#  performs AES-128 encryptions or decryptions like an 8-bit uC would do them
#  and leaks internal state 
# 
#  DESCRIPTION:
# 
#  [result state rkeys mixcolumn_leak] = aes_crypt(input_data, secret_key, encrypt)
# 
#  This function performs an AES-128 encryption or decryption of the input
#  data with the given secret key.
# 
#  PARAMETERS:
# 
#  - input_data:
#    A matrix of bytes, where each line consists of a 16 bytes (128 bit)
#    data input value of the AES-128 en/decryption.
#  - secret_key:
#    A vector of 16 bytes that represents the secret key.
#  - encrypt:
#    Paramter indicating whether an encryption or a decryption is performed
#    (1=encryption, 0=decryption).
# 
#  RETURNVALUES:
# 
#  - result:
#    A matrix of bytes of the same size as the byte matrix 'input_data'.
#    Each line of this matrix consists of 16 bytes that represent the
#    128-bit output of an AES-128 en/decryption of the corresponding line of
#    'input_data'.
#  - state:
#    A matrix of byte of size |'input_data'| x 41, containins the state
#    progression of the encryption process.  
#    Legend of the state progression:
#    (P= plaintext, C=Ciphertext, K=after AddKey, B=after SubBytes, R=after
#    ShiftRows, M=after MixColumns)
#    P K BRMK BRMK BRMK BRMK BRMK BRMK BRMK BRMK BRMK BRK(=C)
#  - mixcolumn_leak:
#    A matrix of size |'input_data'| x 9 x 4 x 9 (for encryption), or
#                     |'input_data'| x 9 x 4 x 18 (for decryption),
#        where mixcolumn_leak(line, subround, col, :) is the list of
#        intermediate valutes generated by the 8-bit MC operation on the
#        [col] columns of line [line] in the input data during
#        subroun [subround]
#  EXAMPLE:
# 
#  result = aes_crypt([1:16; 17:32], 1:16, 1)


#  AUTHORS: Stefan Mangard, Mario Kirschbaum, Yossi Oren
# 
#  CREATION_DATE: 31 July 2001
#  LAST_REVISION: 28 October 2008


def aes_crypt_8bit_and_leak(input_data, secret_key, encrypt):
	list = [41]
	for item in np.shape(input_data):
		list += [item]
	state = np.zeros(list, dtype=np.uint8)
	rkeys = np.zeros([10, 16], dtype=np.uint8)
	if encrypt == 0:  # decryption
		mixcolumn_leak = np.zeros([9, 4, np.shape(input_data)[0], 18])
	else:  # encryption
		mixcolumn_leak = np.zeros([9, 4, np.shape(input_data)[0], 9])
	
	for round in range(10):
		rkeys[round, :] = aes_round_key(secret_key, round)
	
	#  expand the keys
	
	if encrypt == 0:  # decryption
		state[40, :] = input_data
	
		for i in range(9, -1, -1):
			if i != 9:
				input_data = aes_add_round_key(aes_round_key(secret_key, i), input_data)
				state[2 + i*4 + 2, :] = input_data
	
				[input_data, leak] = aes_mix_columns_8bit_and_leak(input_data, 0)
				mixcolumn_leak[i, :, :, :] = leak
				state[2 + i*4 + 1, :] = input_data
			else:
				input_data = aes_add_round_key(aes_round_key(secret_key, i), input_data)
				state[2 + i*4 + 1, :] = input_data
	
			input_data = aes_shift_rows(input_data, 0)
			state[2 + i*4, :] = input_data
	
			input_data = np.uint8(aes_sbox(input_data, 0))
			state[2 + i*4 - 1, :] = input_data
	
		input_data = aes_add_round_key(secret_key, input_data)
		state[0, :] = input_data
	
	else:  # encryption
	
		state[0, :] = np.copy(input_data)
		input_data = aes_add_round_key(secret_key, input_data)
		state[1, :] = np.copy(input_data)
	
	for i in range(10):
			input_data = np.uint8(aes_sbox(input_data, 1))
			state[2 + i*4, :] = np.copy(input_data)
	
			input_data = aes_shift_rows(input_data, 1)
			state[2 + i*4 + 1, :] = np.copy(input_data)
	
			if i != 9:
				[input_data, leak] = aes_mix_columns_8bit_and_leak(input_data, 1)
				mixcolumn_leak[i, :, :, :] = np.copy(leak)

				state[2 + i*4 + 2, :] = np.copy(input_data)
	
				input_data = aes_add_round_key(aes_round_key(secret_key, i), input_data)
				state[2 + i*4 + 3, :] = np.copy(input_data)
			else:
				input_data = aes_add_round_key(aes_round_key(secret_key, i), input_data)
				state[2 + i*4 + 2, :] = np.copy(input_data)

	result = np.copy(input_data)
	return result, state, rkeys, mixcolumn_leak
