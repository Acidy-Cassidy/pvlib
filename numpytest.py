








#!/usr/bin/env python3
import numpy as np2
import mynumpy as np



def numtest():
    
    print("Numpy (My version)")
    c = np.array([1,2,3,4])
    d = np.array([10, 20, 30, 40])
    print('\nArray c:', c)
    print('Array d:', d)
    matrix = np.array([[1, 2], [3,4]])
    print('\nMatrix test:\n', matrix)
    print('Matrix determinant test:', np.linalg.det(matrix))


    

def numpog():
    print("NumPy version:", np2.__version__)

    # Create arrays
    a = np2.array([1, 2, 3, 4])
    b = np2.array([10, 20, 30, 40])

    print("\nArray a:", a)
    print("Array b:", b)

    # Matrix operations
    m = np2.array([[1, 2],
                  [3, 4]])
    print("\nMatrix m:\n", m)
    print("Matrix determinant:", np2.linalg.det(m))

    # Statistics
    data = np2.array([5, 10, 15, 20, 25])
    print("\nMean:", np2.mean(data))
    print("Std Dev:", np2.std(data))

    print("\n✅ NumPy basic test completed successfully")

def main():
    
    numpog()
    numtest()
if __name__ == "__main__":
    main()

