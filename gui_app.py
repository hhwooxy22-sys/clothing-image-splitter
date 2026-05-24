import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import pytesseract
import json
import os
from pathlib import Path
from datetime import datetime
import threading

class ClothingImageSplitterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("의류 이미지 그리드 분할 프로그램")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # 색상 설정
        self.bg_color = "#f0f0f0"
        self.root.configure(bg=self.bg_color)
        
        self.input_image_path = None
        self.output_dir = "output"
        
        self.setup_ui()
        
    def setup_ui(self):
        """UI 설정"""
        # 제목
        title_label = tk.Label(
            self.root,
            text="🎨 의류 이미지 분할 프로그램",
            font=("Arial", 16, "bold"),
            bg=self.bg_color
        )
        title_label.pack(pady=20)
        
        # 설명
        desc_label = tk.Label(
            self.root,
            text="옷 사진을 선택하면 자동으로 개별 이미지와 메타데이터를 추출합니다.",
            font=("Arial", 10),
            bg=self.bg_color,
            wraplength=550
        )
        desc_label.pack(pady=10)
        
        # 파일 선택 버튼
        self.file_button = tk.Button(
            self.root,
            text="📁 이미지 파일 선택",
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            padx=30,
            pady=15,
            command=self.select_image,
            cursor="hand2"
        )
        self.file_button.pack(pady=20)
        
        # 선택된 파일 표시
        self.file_label = tk.Label(
            self.root,
            text="선택된 파일: 없음",
            font=("Arial", 10),
            bg=self.bg_color,
            fg="#666"
        )
        self.file_label.pack(pady=10)
        
        # 진행 상황 표시
        self.progress_var = tk.StringVar(value="준비 중...")
        self.status_label = tk.Label(
            self.root,
            textvariable=self.progress_var,
            font=("Arial", 10),
            bg=self.bg_color,
            fg="#2196F3"
        )
        self.status_label.pack(pady=10)
        
        # 프로그레스 바
        self.progress_bar = ttk.Progressbar(
            self.root,
            mode="indeterminate",
            length=400
        )
        self.progress_bar.pack(pady=15)
        
        # 실행 버튼
        self.run_button = tk.Button(
            self.root,
            text="▶ 실행",
            font=("Arial", 12, "bold"),
            bg="#2196F3",
            fg="white",
            padx=30,
            pady=15,
            command=self.run_splitter,
            cursor="hand2",
            state="disabled"
        )
        self.run_button.pack(pady=10)
        
        # 결과 표시
        self.result_label = tk.Label(
            self.root,
            text="",
            font=("Arial", 10),
            bg=self.bg_color,
            fg="#4CAF50",
            wraplength=550
        )
        self.result_label.pack(pady=10)
        
        # 폴더 열기 버튼
        self.open_folder_button = tk.Button(
            self.root,
            text="📂 결과 폴더 열기",
            font=("Arial", 10),
            bg="#FF9800",
            fg="white",
            padx=20,
            pady=10,
            command=self.open_output_folder,
            cursor="hand2",
            state="disabled"
        )
        self.open_folder_button.pack(pady=5)
        
    def select_image(self):
        """이미지 파일 선택"""
        file_path = filedialog.askopenfilename(
            title="이미지 파일 선택",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif"),
                ("JPG files", "*.jpg *.jpeg"),
                ("PNG files", "*.png"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.input_image_path = file_path
            filename = os.path.basename(file_path)
            self.file_label.config(text=f"선택된 파일: {filename}", fg="#333")
            self.run_button.config(state="normal")
            self.result_label.config(text="")
            
    def run_splitter(self):
        """프로그램 실행"""
        if not self.input_image_path:
            messagebox.showerror("오류", "이미지 파일을 먼저 선택하세요!")
            return
        
        # 스레드에서 실행 (UI 프리징 방지)
        thread = threading.Thread(target=self.process_image)
        thread.start()
        
    def process_image(self):
        """이미지 처리"""
        try:
            self.progress_bar.start()
            self.run_button.config(state="disabled")
            self.file_button.config(state="disabled")
            self.progress_var.set("처리 중... 이미지 로드")
            
            # ClothingImageSplitter 실행
            splitter = ClothingImageSplitter(
                self.input_image_path,
                self.output_dir
            )
            
            self.progress_var.set("처리 중... 의류 영역 감지")
            splitter.load_image()
            
            self.progress_var.set("처리 중... 영역 분할")
            clothing_regions = splitter.detect_clothing_regions()
            
            if not clothing_regions:
                self.progress_bar.stop()
                messagebox.showwarning(
                    "경고",
                    "의류 영역을 감지하지 못했습니다.\n\n더 명확한 이미지를 사용해주세요."
                )
                self.progress_var.set("준비 중...")
                self.run_button.config(state="normal")
                self.file_button.config(state="normal")
                return
            
            self.progress_var.set("처리 중... 이미지 분할")
            results = splitter.split_and_save(clothing_regions)
            
            self.progress_var.set("처리 중... 메타데이터 저장")
            splitter.save_metadata(results)
            
            self.progress_bar.stop()
            
            # 성공 메시지
            success_msg = f"✓ 처리 완료!\n\n{len(results)}개의 의류 이미지가 생성되었습니다.\n\n폴더: {os.path.abspath(self.output_dir)}"
            messagebox.showinfo("성공", success_msg)
            
            self.progress_var.set(f"✓ {len(results)}개 이미지 생성 완료!")
            self.result_label.config(
                text=f"✓ {len(results)}개의 의류 이미지가 생성되었습니다!",
                fg="#4CAF50"
            )
            self.open_folder_button.config(state="normal")
            
        except Exception as e:
            self.progress_bar.stop()
            messagebox.showerror("오류", f"처리 중 오류 발생:\n\n{str(e)}")
            self.progress_var.set("오류 발생")
            self.result_label.config(text="오류 발생", fg="#f44336")
        
        finally:
            self.run_button.config(state="normal")
            self.file_button.config(state="normal")
            
    def open_output_folder(self):
        """결과 폴더 열기"""
        output_path = os.path.abspath(self.output_dir)
        if os.path.exists(output_path):
            os.startfile(output_path)  # Windows
        else:
            messagebox.showerror("오류", "결과 폴더를 찾을 수 없습니다.")


class ClothingImageSplitter:
    def __init__(self, input_image_path, output_dir="output"):
        """의류 이미지 그리드 분할 및 메타데이터 추출기 초기화"""
        self.input_image_path = input_image_path
        self.output_dir = output_dir
        self.image = None
        self.gray_image = None
        
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
    def load_image(self):
        """이미지 로드"""
        self.image = cv2.imread(self.input_image_path)
        if self.image is None:
            raise ValueError(f"이미지를 로드할 수 없습니다: {self.input_image_path}")
        
        self.gray_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        
    def detect_clothing_regions(self):
        """의류 영역 자동 감지"""
        blurred = cv2.GaussianBlur(self.gray_image, (5, 5), 0)
        _, binary = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY)
        
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        clothing_regions = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 5000:
                continue
                
            x, y, w, h = cv2.boundingRect(contour)
            
            aspect_ratio = h / w if w > 0 else 0
            if aspect_ratio < 0.5 or aspect_ratio > 3:
                continue
            
            clothing_regions.append({
                'x': x,
                'y': y,
                'w': w,
                'h': h,
                'area': area,
                'contour': contour
            })
        
        clothing_regions.sort(key=lambda r: r['x'])
        
        return clothing_regions
    
    def extract_metadata_from_image(self, roi):
        """이미지 영역에서 메타데이터 추출"""
        metadata = {
            'brand': '',
            'product_name': '',
            'price': '',
            'discount': '',
            'color': self.detect_dominant_color(roi),
            'pattern': self.detect_pattern(roi),
            'extracted_text': ''
        }
        
        try:
            roi_pil = Image.fromarray(cv2.cvtColor(roi, cv2.COLOR_BGR2RGB))
            
            try:
                extracted_text = pytesseract.image_to_string(roi_pil, lang='kor+eng')
                metadata['extracted_text'] = extracted_text.strip()
                
                lines = extracted_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if '원' in line:
                        metadata['price'] = line
                    elif '%' in line:
                        metadata['discount'] = line
                    elif len(line) > 5 and line[0].isalpha():
                        if not metadata['product_name']:
                            metadata['product_name'] = line
                        elif not metadata['brand']:
                            metadata['brand'] = line
            except:
                pass  # OCR 실패해도 계속 진행
        
        except Exception as e:
            pass
        
        return metadata
    
    def detect_dominant_color(self, roi):
        """주요 색상 감지"""
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        color_ranges = {
            'red': ((0, 100, 100), (10, 255, 255)),
            'yellow': ((20, 100, 100), (30, 255, 255)),
            'green': ((40, 100, 100), (80, 255, 255)),
            'cyan': ((80, 100, 100), (100, 255, 255)),
            'blue': ((100, 100, 100), (130, 255, 255)),
            'magenta': ((130, 100, 100), (170, 255, 255)),
        }
        
        max_count = 0
        detected_color = 'unknown'
        
        for color_name, (lower, upper) in color_ranges.items():
            lower = np.array(lower)
            upper = np.array(upper)
            mask = cv2.inRange(hsv, lower, upper)
            count = cv2.countNonZero(mask)
            
            if count > max_count:
                max_count = count
                detected_color = color_name
        
        return detected_color
    
    def detect_pattern(self, roi):
        """패턴 감지"""
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        edges = cv2.Canny(gray, 100, 200)
        
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 50, minLineLength=50, maxLineGap=10)
        
        if lines is None:
            return 'solid'
        
        vertical_lines = sum(1 for line in lines if abs(line[0][0] - line[0][2]) < 5)
        horizontal_lines = sum(1 for line in lines if abs(line[0][1] - line[0][3]) < 5)
        
        total_lines = len(lines)
        
        if vertical_lines > total_lines * 0.6:
            return 'vertical_stripe'
        elif horizontal_lines > total_lines * 0.6:
            return 'horizontal_stripe'
        elif vertical_lines > 3 and horizontal_lines > 3:
            return 'checkered'
        else:
            return 'solid'
    
    def split_and_save(self, clothing_regions):
        """의류 영역을 분할하여 저장"""
        results = []
        
        for idx, region in enumerate(clothing_regions, 1):
            x, y, w, h = region['x'], region['y'], region['w'], region['h']
            clothing_image = self.image[y:y+h, x:x+w]
            
            output_filename = f"{idx}.jpg"
            output_path = os.path.join(self.output_dir, output_filename)
            
            cv2.imwrite(output_path, clothing_image)
            
            metadata = self.extract_metadata_from_image(clothing_image)
            metadata['number'] = idx
            metadata['image_file'] = output_filename
            metadata['region'] = {
                'x': int(x),
                'y': int(y),
                'width': int(w),
                'height': int(h)
            }
            
            results.append(metadata)
        
        return results
    
    def save_metadata(self, results):
        """메타데이터를 JSON으로 저장"""
        metadata_path = os.path.join(self.output_dir, "metadata.json")
        
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'source_image': self.input_image_path,
            'total_items': len(results),
            'items': results
        }
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)


def main():
    root = tk.Tk()
    app = ClothingImageSplitterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
