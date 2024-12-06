import cv2
import numpy as np
import pytesseract
from PIL import Image
import logging

def preprocess_image(image_path):
    """Advanced image preprocessing for better OCR accuracy"""
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    _, thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = np.ones((3,3), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
    return thresh

def extract_sudoku_grid(preprocessed_image):
    """Detect and extract Sudoku grid from the image"""
    contours, _ = cv2.findContours(preprocessed_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    largest_contour = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest_contour)
    grid = preprocessed_image[y:y+h, x:x+w]
    return grid

def ocr_sudoku_grid(grid_image):
    """Advanced OCR with multiple recognition attempts"""
    configurations = [
        '--psm 6 outputbase digits',
        '--psm 3 outputbase digits',
        '--psm 4 outputbase digits',
    ]
    
    for config in configurations:
        try:
            ocr_result = pytesseract.image_to_string(
                Image.fromarray(grid_image), 
                config=config
            )
            board = parse_ocr_result(ocr_result)
            if is_valid_board(board):
                return board
        except Exception as e:
            logging.warning(f"OCR attempt failed with config {config}: {e}")
    
    raise ValueError("Could not extract Sudoku grid")

def parse_ocr_result(ocr_result):
    """Parse OCR result into a 2D grid"""
    board = [[0 for _ in range(9)] for _ in range(9)]
    lines = ocr_result.strip().split('\n')
    
    for i, line in enumerate(lines):
        if i >= 9:
            break
        
        digits = [int(d) if d.isdigit() else 0 for d in line.split()]
        
        for j, digit in enumerate(digits):
            if j >= 9:
                break
            board[i][j] = digit
    
    return board

def is_valid_board(board):
    """Validate extracted board"""
    if len(board) != 9 or any(len(row) != 9 for row in board):
        return False
    
    for row in board:
        if any(not (0 <= num <= 9) for num in row):
            return False
    
    return True

def solve_sudoku_board(board):
    """Backtracking Sudoku solver"""
    def find_empty_cell(board):
        for i in range(9):
            for j in range(9):
                if board[i][j] == 0:
                    return i, j
        return None

    def is_valid_move(board, num, pos):
        # Check row
        for j in range(9):
            if board[pos[0]][j] == num and pos[1] != j:
                return False

        # Check column
        for i in range(9):
            if board[i][pos[1]] == num and pos[0] != i:
                return False

        # Check 3x3 box
        box_x, box_y = pos[1] // 3, pos[0] // 3
        for i in range(box_y * 3, box_y * 3 + 3):
            for j in range(box_x * 3, box_x * 3 + 3):
                if board[i][j] == num and (i, j) != pos:
                    return False

        return True

    def solve(board):
        empty_cell = find_empty_cell(board)
        if not empty_cell:
            return True
        
        row, col = empty_cell
        
        for num in range(1, 10):
            if is_valid_move(board, num, (row, col)):
                board[row][col] = num
                
                if solve(board):
                    return True
                
                board[row][col] = 0
        
        return False

    board_copy = [row[:] for row in board]
    
    if solve(board_copy):
        return board_copy
    else:
        raise ValueError("No solution exists for this Sudoku puzzle")

def visualize_sudoku_solution(original_img, solved_board, original_board):
    """Visualize complete Sudoku solution"""
    cell_size = original_img.shape[0] // 9
    solved_img = original_img.copy()
    font = cv2.FONT_HERSHEY_SIMPLEX

    for i in range(9):
        for j in range(9):
            top_left = (j * cell_size, i * cell_size)
            bottom_right = ((j + 1) * cell_size, (i + 1) * cell_size)
            cv2.rectangle(solved_img, top_left, bottom_right, (0, 0, 0), 2)

            # Prioritize original numbers, fill in solved numbers
            if original_board[i][j] != 0:
                cv2.putText(solved_img, str(original_board[i][j]), 
                            (top_left[0] + 15, top_left[1] + 35), 
                            font, 1, (0, 0, 0), 2, cv2.LINE_AA)
            elif solved_board[i][j] != 0:
                cv2.putText(solved_img, str(solved_board[i][j]), 
                            (top_left[0] + 15, top_left[1] + 35), 
                            font, 1, (0, 0, 0), 2, cv2.LINE_AA)

    return solved_img

def solve_sudoku(input_image_path, output_image_path):
    """Main Sudoku solving workflow"""
    try:
        # Preprocess image
        preprocessed_image = preprocess_image(input_image_path)
        
        # Extract grid
        grid = extract_sudoku_grid(preprocessed_image)
        
        # Perform OCR
        original_board = ocr_sudoku_grid(grid)
        
        # Solve Sudoku
        solved_board = solve_sudoku_board(original_board)
        
        # Read original image for visualization
        original_img = cv2.imread(input_image_path)
        
        # Visualize solution
        solved_img = visualize_sudoku_solution(original_img, solved_board, original_board)
        
        # Save solved image
        cv2.imwrite(output_image_path, solved_img)
        
        return solved_board

    except Exception as e:
        logging.error(f"Sudoku solving error: {e}")
        raise
