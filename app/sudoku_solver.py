import cv2
import pytesseract
from PIL import Image
import numpy as np
import os
import logging

def solve_sudoku_board(board):
    empty = find_empty(board)
    if not empty:
        return board
    row, col = empty

    for num in range(1, 10):
        if valid(board, num, (row, col)):
            board[row][col] = num
            if solve_sudoku_board(board):
                return board
            board[row][col] = 0

    return None

def valid(board, num, pos):
    row, col = pos
    for i in range(9):
        if board[row][i] == num or board[i][col] == num:
            return False

    box_x, box_y = col // 3, row // 3
    for i in range(box_y * 3, box_y * 3 + 3):
        for j in range(box_x * 3, box_x * 3 + 3):
            if board[i][j] == num:
                return False

    return True

def find_empty(board):
    for i in range(9):
        for j in range(9):
            if board[i][j] == 0:
                return (i, j)
    return None

def image_to_sudoku_board(image):
    # Convert image to grayscale and threshold
    image = image.convert('L')
    image = image.point(lambda x: 0 if x < 128 else 255, '1')

    # Perform OCR
    data = pytesseract.image_to_string(image, config='--psm 6 outputbase digits')
    lines = data.splitlines()
    
    # Initialize a 9x9 board with zeros
    board = [[0 for _ in range(9)] for _ in range(9)]
    
    # Parse recognized digits
    for i, line in enumerate(lines):
        if i >= 9:  # Limit to 9 rows
            break
        
        row_nums = [int(num) if num.isdigit() else 0 for num in line.split()]
        for j, num in enumerate(row_nums):
            if j >= 9:  # Limit to 9 columns
                break
            board[i][j] = num

    return board

def solve_sudoku(input_image_path, output_image_path):
    try:
        # Read images
        img = cv2.imread(input_image_path)
        pil_img = Image.open(input_image_path)

        # Convert image to board
        board = image_to_sudoku_board(pil_img)
        
        # Validate board
        if not board or len(board) != 9 or any(len(row) != 9 for row in board):
            raise ValueError("Invalid Sudoku board detected")

        # Solve board
        solved_board = solve_sudoku_board([row[:] for row in board])
        
        if solved_board is None:
            raise ValueError("No solution exists for this Sudoku puzzle")

        # Visualize solution
        solved_img = visualize_sudoku_on_image(img, solved_board)
        cv2.imwrite(output_image_path, solved_img)
        
        return solved_board

    except Exception as e:
        logging.error(f"Sudoku solving error: {e}")
        raise

def visualize_sudoku_on_image(img, board):
    cell_size = 50
    font = cv2.FONT_HERSHEY_SIMPLEX
    solved_img = img.copy()

    for i in range(9):
        for j in range(9):
            top_left = (j * cell_size, i * cell_size)
            bottom_right = ((j + 1) * cell_size, (i + 1) * cell_size)
            cv2.rectangle(solved_img, top_left, bottom_right, (0, 0, 0), 2)

            if board[i][j] != 0:
                cv2.putText(solved_img, str(board[i][j]), 
                            (top_left[0] + 15, top_left[1] + 35), 
                            font, 1, (0, 0, 0), 2, cv2.LINE_AA)

    return solved_img
