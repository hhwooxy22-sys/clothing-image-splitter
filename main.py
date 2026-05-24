import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import pytesseract
import json
import os
from pathlib import Path
from datetime import datetime

class ClothingImageSplitter:
    def __init__(self, input_image_path, output_dir="output"):
        """
        의류 이미지 그리드 분할 및 메타데이터 추출기 초기화
        
        Args:
            input_image_path: 입력 이미지 경로
            output_dir: 출력 디렉토리
        """
        self.input_image_path = input_image_path
        self.output_dir = output_dir
        self.image = None
        self.gray_image = None
        self.clothing_items = []
        
        # 출력 디렉토리 생성
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
    def load_image(self):
        """이미지 로드"""
        self.image = cv2.imread(self.input_image_path)
        if self.image is None:
            raise ValueError(f"이미지를 로드할 수 없습니다: {self.input_image_path}")
        
        self.gray_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        print(f"✓ 이미지 로드 완료: {self.input_image_path}")
        print(f"  이미지 크기: {self.image.shape}")
        
    def detect_clothing_regions(self):
        """
        의류 영역 자동 감지
        이미지에서 번호가 있는 의류 영역을 찾음
        """
        # 이미지 전처리
        blurred = cv2.GaussianBlur(self.gray_image, (5, 5), 0)
        _, binary = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY)
        
        # 컨투어 찾기
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 의류 영역 필터링 및 정렬
        clothing_regions = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            # 최소 크기 필터링 (너무 작은 영역 제외)
            if area < 5000:
                continue
                
            x, y, w, h = cv2.boundingRect(contour)
            
            # 종횡비 필터링 (의류는 보통 세로가 더 김)
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
        
        # x 좌표 기준으로 정렬 (왼쪽에서 오른쪽)
        clothing_regions.sort(key=lambda r: r['x'])
        
        print(f"✓ {len(clothing_regions)}개의 의류 영역 감지됨")
        return clothing_regions
    
    def extract_metadata_from_image(self, roi):
        """
        이미지 영역에서 메타데이터 추출
        OCR을 사용하여 텍스트 추출
        
        Args:
            roi: 관심 영역 (Region of Interest)
        
        Returns:
            메타데이터 딕셔너리
        """
        metadata = {
            'brand': '',
            'product_name': '',
            'price': '',
            'discount': '',
            'color': self.detect_dominant_color(roi),
            'pattern': self.detect_pattern(roi),
            'extracted_text': ''
        }
        
        # OCR을 사용하여 텍스트 추출
        try:
            # PIL 이미지로 변환
            roi_pil = Image.fromarray(cv2.cvtColor(roi, cv2.COLOR_BGR2RGB))
            
            # OCR 실행
            extracted_text = pytesseract.image_to_string(roi_pil, lang='kor+eng')
            metadata['extracted_text'] = extracted_text.strip()
            
            # 텍스트 파싱
            lines = extracted_text.split('\n')
            for line in lines:
                line = line.strip()
                if '원' in line:  # 가격 추출
                    metadata['price'] = line
                elif '%' in line:  # 할인율 추출
                    metadata['discount'] = line
                elif len(line) > 5 and line[0].isalpha():  # 제품명 추출
                    if not metadata['product_name']:
                        metadata['product_name'] = line
                    elif not metadata['brand']:
                        metadata['brand'] = line
        
        except Exception as e:
            print(f"⚠ OCR 오류: {e}")
        
        return metadata
    
    def detect_dominant_color(self, roi):
        """
        ROI에서 주요 색상 감지
        
        Args:
            roi: 관심 영역
        
        Returns:
            색상명
        """
        # BGR을 HSV로 변환
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        # 색상 범위 정의
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
        """
        ROI에서 패턴 감지 (줄무늬, 격자 등)
        
        Args:
            roi: 관심 영역
        
        Returns:
            패턴명
        """
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # 엣지 감지
        edges = cv2.Canny(gray, 100, 200)
        
        # 직선 감지
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 50, minLineLength=50, maxLineGap=10)
        
        if lines is None:
            return 'solid'
        
        # 수직선 개수
        vertical_lines = sum(1 for line in lines if abs(line[0][0] - line[0][2]) < 5)
        # 수평선 개수
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
        """
        의류 영역을 분할하여 저장
        
        Args:
            clothing_regions: 의류 영역 리스트
        """
        results = []
        
        for idx, region in enumerate(clothing_regions, 1):
            # 의류 이미지 추출
            x, y, w, h = region['x'], region['y'], region['w'], region['h']
            clothing_image = self.image[y:y+h, x:x+w]
            
            # 파일명
            output_filename = f"{idx}.jpg"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # 이미지 저장
            cv2.imwrite(output_path, clothing_image)
            
            # 메타데이터 추출
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
            
            print(f"✓ {idx}번 의류 저장 완료:")
            print(f"  파일: {output_filename}")
            print(f"  색상: {metadata['color']}")
            print(f"  패턴: {metadata['pattern']}")
            print(f"  가격: {metadata['price']}")
        
        return results
    
    def save_metadata(self, results):
        """
        메타데이터를 JSON으로 저장
        
        Args:
            results: 메타데이터 리스트
        """
        metadata_path = os.path.join(self.output_dir, "metadata.json")
        
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'source_image': self.input_image_path,
            'total_items': len(results),
            'items': results
        }
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ 메타데이터 저장 완료: {metadata_path}")
    
    def run(self):
        """전체 프로세스 실행"""
        try:
            print("=" * 50)
            print("의류 이미지 그리드 분할 프로그램 시작")
            print("=" * 50)
            
            # 1. 이미지 로드
            self.load_image()
            
            # 2. 의류 영역 감지
            clothing_regions = self.detect_clothing_regions()
            
            if not clothing_regions:
                print("⚠ 의류 영역을 감지하지 못했습니다.")
                return
            
            # 3. 의류 분할 및 저장
            print("\n의류 이미지 분할 중...")
            results = self.split_and_save(clothing_regions)
            
            # 4. 메타데이터 저장
            self.save_metadata(results)
            
            print("\n" + "=" * 50)
            print(f"✓ 처리 완료!")
            print(f"  출력 디렉토리: {self.output_dir}")
            print("=" * 50)
            
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            raise


def main():
    """메인 함수"""
    # 사용 예시
    input_image = "input_image.jpg"  # 입력 이미지 경로
    
    if not os.path.exists(input_image):
        print(f"오류: {input_image} 파일이 없습니다.")
        print("입력 이미지를 '{input_image}'로 저장하고 다시 실행해주세요.")
        return
    
    splitter = ClothingImageSplitter(input_image_path=input_image, output_dir="output")
    splitter.run()


if __name__ == "__main__":
    main()
