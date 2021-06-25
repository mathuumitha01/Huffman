import sys
import argparse
import shutil

#huffman tree class
class node(object):
    def __init__(self,value=None,left=None,right=None,root=None):
        self.value=value
        self.left=left
        self.right=right
        self.root=root 

#Building the tree
def creat_tree(nodes_list):
    nodes_list.sort(key=lambda x: x.value)      
    if len(nodes_list)==1:
        return nodes_list[0]        
    root_node=node(nodes_list[0].value+nodes_list[1].value,nodes_list[0],nodes_list[1]) 
    nodes_list[0].root=nodes_list[1].root=root_node
    nodes_list.pop(0)
    nodes_list.pop(0)
    nodes_list.insert(0,root_node)   
    return creat_tree(nodes_list)

def node_encode(node1):            
    if node1.root==None:
        return b''
    if node1.root.left==node1:
        return node_encode(node1.root)+b'0'
    else:
        return node_encode(node1.root)+b'1'

def encode(input_file,output_file):
    print("encoding ", input_file, output_file)
    with open(input_file,'rb') as f:
        f.seek(0, 2)        
        size=f.tell()
        f.seek(0)
        bytes_list=[0]*size  

        i=0
        while i<size:
            bytes_list[i]=f.read(1)  
            i+=1

    count_dict = {}  # Use a dictionary to count the number of occurrences
    for x in bytes_list:
        if x not in count_dict.keys():
            count_dict[x] = 0
        count_dict[x] += 1

    node_dict={}   
    for x in count_dict.keys():
        node_dict[x]=node(count_dict[x])  

    nodes=[]      #list to save nodes 
    for x in node_dict.keys():
        nodes.append(node_dict[x])

    root=creat_tree(nodes)   

    #Encoding leaf nodes 
    bytes_dict={}
    for x in node_dict.keys():
        bytes_dict[x]=node_encode(node_dict[x])

    name=input_file.split('/')[-1]
    with open(output_file,'wb') as object:
        #First write the original name of the file
        object.write((name+'\n').encode(encoding='UTF-8'))
        n=len(count_dict.keys())
        object.write(int.to_bytes(n ,2 ,byteorder = 'big'))

        times=0
        for x in count_dict.keys():
            if times<count_dict[x]:
                times=count_dict[x]
        width=1
        if times>255:
            width=2
            if times>65535:
                width=3
                if times>16777215:
                    width=4
        
        object.write(int.to_bytes(width,1,byteorder='big'))

        for x in count_dict.keys():
            object.write(x)
            object.write(int.to_bytes(count_dict[x], width, byteorder='big'))

        code=b''     
        for x in bytes_list:
            code+=bytes_dict[x]
            out=0
            while len(code)>=8:
                for s in range(8):
                    out = out << 1
                    if code[s] == 49:    #ASCII code 1=49
                        out = out | 1
                object.write(int.to_bytes(out,1,byteorder='big'))
                out=0
                code=code[8:]

        #Processing data less than one byte
        object.write(int.to_bytes(len(code), 1, byteorder='big')) 
        out=0
        for i in range(len(code)):
            out = out << 1
            if code[i] == 49:
                out = out | 1
        object.write(int.to_bytes(out,1,byteorder='big'))
        print('Sucessful')


#Before decoding, revisit the contents of the compressed file.The first line is the original file name
#The first two bytes of the second line record the number of nodes n, then one byte records the bit width of the frequency, and then records each byte and its frequency
def decode(input_file,output_file):
    print("decoding ", input_file, output_file)
    with open(input_file,'rb') as f_in:

        f_in.seek(0,2)
        length=f_in.tell() #read length of the file
        f_in.seek(0)

        name = f_in.readline().decode(encoding="UTF-8").split('/')[-1].replace('\n','')
        name = name.split('.')[-1]                   #Read out the file name
        with open(output_file,'wb') as f_out:
            n=int.from_bytes(f_in.read(2), byteorder = 'big')     #number of nodes
            width=int.from_bytes(f_in.read(1), byteorder = 'big') #bit width
            count_dict={}
            i=0
            while i<n:
                dict_key=f_in.read(1)
                dict_value=int.from_bytes(f_in.read(width),byteorder='big')
                count_dict[dict_key]=dict_value
                i+=1

            node_dict = {} 
            for x in count_dict.keys():
                node_dict[x] = node(count_dict[x])  


            nodes = []  #list to save nodes
            for x in node_dict.keys():
                nodes.append(node_dict[x])

            root = creat_tree(nodes)  

            #Encode leaf nodes 
            bytes_dict = {}
            for x in node_dict.keys():
                bytes_dict[x] = node_encode(node_dict[x])

            diff_dict={}
            for x in bytes_dict.keys():
                diff_dict[bytes_dict[x]]=x

            #When decoding, read a single number, traverse the binary tree until the leaf node is found
            out=b''
            i=f_in.tell()
            node_now = root
            result = b''
            while i < length-2:
                i+=1
                temp=int.from_bytes(f_in.read(1),byteorder='big')
                for mm in range(8):        #Convert data to b'01 'form
                    if temp&1 == 1:
                        out=b'1'+out
                    else:
                        out=b'0'+out
                    temp=temp>>1

                while out:       #Traversing the Huffman tree
                    if out[0]==49:
                        node_now=node_now.right
                        result = result+b'1'
                    if out[0]==48:
                        node_now=node_now.left
                        result = result+b'0'
                    out=out[1:]
                    if node_now.left==None and node_now.right==None:
                        f_out.write(diff_dict[result])
                        result=b''
                        node_now=root

            # Processing the last data than 8 bits
            last_length = int.from_bytes(f_in.read(1), byteorder='big')
            temp= int.from_bytes(f_in.read(1), byteorder='big')
            for mm in range(last_length):  # Converting data to b'01' form
                if temp & 1 == 1:
                    out = b'1' + out
                else:
                    out = b'0' + out
                temp = temp >> 1
            while out:  #huffman tree
                if out[0] == 49:
                    node_now = node_now.right
                    result = result + b'1'
                if out[0] == 48:
                    node_now = node_now.left
                    result = result + b'0'
                out = out[1:]
                if node_now.left == None and node_now.right == None:
                    f_out.write(diff_dict[result])
                    result = b''
                    node_now = root
    print('Sucessful')

def get_options(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description="Huffman compression.")
    groups = parser.add_mutually_exclusive_group(required=True)
    groups.add_argument("-e", type=str, help="Encode files")
    groups.add_argument("-d", type=str, help="Decode files")
    parser.add_argument("-o", type=str, help="Write encoded/decoded file", required=True)
    options = parser.parse_args()
    return options

if __name__ == '__main__':
    options=get_options()
    if options.e is not None:
        encode(options.e,options.o)
    if options.d is not None:
        decode(options.d,options.o)