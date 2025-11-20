import os
import cv2
import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import hashlib
import base64
from tkinter import Tk, filedialog
import json
from datetime import datetime
import imagehash

class ImageImportProcessor:
    """图像导入处理器 - 支持数字指纹和持久化存储"""
    
    def __init__(self, storage_file='image_fingerprints.json'):
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
        self.loaded_images = {}
        
        # 使用绝对路径存储数据库文件
        if not os.path.isabs(storage_file):
            # 将相对路径转换为脚本所在目录的绝对路径
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.storage_file = os.path.join(script_dir, storage_file)
        else:
            self.storage_file = storage_file
            
        self.fingerprint_database = {}  # 指纹数据库
        
        # 启动时加载历史记录
        print(f"📂 数据库文件位置: {self.storage_file}")
        self.load_fingerprint_database()
    
    def check_image_format(self, file_path):
        """检查图像格式是否支持"""
        _, ext = os.path.splitext(file_path)
        return ext.lower() in self.supported_formats
    
    def load_image_from_path(self, file_path):
        """从文件路径导入图像 - 增强版带指纹识别"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        if not self.check_image_format(file_path):
            raise ValueError(f"不支持的图像格式: {file_path}")
        
        try:
            # 使用PIL加载图像
            pil_image = Image.open(file_path)
            image_array = np.array(pil_image)
            
            # 转换为RGB格式（如果需要）
            if len(image_array.shape) == 2:  # 灰度图
                image_array = cv2.cvtColor(image_array, cv2.COLOR_GRAY2RGB)
            elif image_array.shape[2] == 4:  # RGBA
                image_array = cv2.cvtColor(image_array, cv2.COLOR_RGBA2RGB)
            
            # 生成数字指纹
            fingerprint = self.generate_perceptual_hash(image_array)
            
            # 检查是否是已知图片
            similar_images = self.find_similar_images(fingerprint, threshold=90)
            
            image_info = {
                'array': image_array,
                'path': file_path,
                'size': pil_image.size,
                'mode': pil_image.mode,
                'format': pil_image.format or os.path.splitext(file_path)[1][1:].upper(),
                'filename': os.path.basename(file_path),
                'fingerprint': fingerprint,
                'load_time': datetime.now().isoformat(),
                'file_size': os.path.getsize(file_path)
            }
            
            # 生成图像哈希作为唯一标识
            image_hash = self.generate_image_hash(image_array)
            self.loaded_images[image_hash] = image_info
            
            # 保存指纹到数据库
            self.add_to_fingerprint_database(fingerprint, image_info)
            
            print(f"✓ 图像加载成功: {image_info['filename']}")
            print(f"  尺寸: {image_info['size'][0]}x{image_info['size'][1]}")
            print(f"  格式: {image_info['format']}")
            print(f"  数字指纹: {fingerprint[:32]}...")
            
            # 显示相似图片信息
            if similar_images:
                print(f"\n🔍 发现相似图片:")
                for idx, similar in enumerate(similar_images[:3], 1):
                    print(f"  {idx}. 相似度: {similar['similarity']:.1f}%")
                    print(f"     原始文件: {similar['data']['original_filename']}")
                    print(f"     首次加载: {similar['data']['first_seen']}")
                    if similar['similarity'] > 95:
                        print(f"     ⚠️  这很可能是同一张图片!")
            
            return image_hash, image_info
            
        except Exception as e:
            raise Exception(f"图像加载失败: {str(e)}")
    
    def load_image_from_bytes(self, image_data, format_hint='JPEG'):
        """从字节数据导入图像"""
        try:
            # 将字节数据转换为PIL图像
            pil_image = Image.open(image_data)
            image_array = np.array(pil_image)
            
            image_info = {
                'array': image_array,
                'path': 'memory',
                'size': pil_image.size,
                'mode': pil_image.mode,
                'format': format_hint
            }
            
            image_hash = self.generate_image_hash(image_array)
            self.loaded_images[image_hash] = image_info
            
            return image_hash, image_info
            
        except Exception as e:
            raise Exception(f"字节数据加载失败: {str(e)}")
    
    def generate_image_hash(self, image_array):
        """生成图像哈希值"""
        # 将图像数据转换为字节
        image_bytes = image_array.tobytes()
        # 使用SHA256生成哈希
        hash_object = hashlib.sha256(image_bytes)
        return base64.b64encode(hash_object.digest()).decode('utf-8')[:32]
    
    def generate_perceptual_hash(self, image_array):
        """生成感知哈希(数字指纹) - 图片内容相似则指纹相同"""
        try:
            # 转换为PIL图像
            if image_array.dtype != np.uint8:
                image_array = (image_array * 255).astype(np.uint8)
            pil_image = Image.fromarray(image_array)
            
            # 使用多种哈希算法提高准确性
            ahash = str(imagehash.average_hash(pil_image))
            phash = str(imagehash.phash(pil_image))
            dhash = str(imagehash.dhash(pil_image))
            
            # 组合指纹
            fingerprint = f"{ahash}_{phash}_{dhash}"
            return fingerprint
        except Exception as e:
            print(f"生成指纹失败: {e}")
            return None
    
    def calculate_fingerprint_similarity(self, fp1, fp2):
        """计算两个指纹的相似度 (0-100)"""
        try:
            parts1 = fp1.split('_')
            parts2 = fp2.split('_')
            
            similarities = []
            for p1, p2 in zip(parts1, parts2):
                # 计算汉明距离
                distance = sum(c1 != c2 for c1, c2 in zip(p1, p2))
                max_len = max(len(p1), len(p2))
                similarity = (1 - distance / max_len) * 100
                similarities.append(similarity)
            
            return sum(similarities) / len(similarities)
        except:
            return 0
    
    def find_similar_images(self, fingerprint, threshold=90):
        """在数据库中查找相似图片"""
        similar_images = []
        for fp_id, fp_data in self.fingerprint_database.items():
            similarity = self.calculate_fingerprint_similarity(
                fingerprint, fp_data['fingerprint']
            )
            if similarity >= threshold:
                similar_images.append({
                    'id': fp_id,
                    'similarity': similarity,
                    'data': fp_data
                })
        
        # 按相似度排序
        similar_images.sort(key=lambda x: x['similarity'], reverse=True)
        return similar_images
    
    def get_image_info(self, image_hash):
        """获取图像信息"""
        if image_hash not in self.loaded_images:
            raise KeyError(f"图像未找到: {image_hash}")
        return self.loaded_images[image_hash]
    
    def display_image_info(self, image_hash):
        """显示图像基本信息"""
        info = self.get_image_info(image_hash)
        print(f"图像哈希: {image_hash}")
        print(f"文件路径: {info['path']}")
        print(f"图像尺寸: {info['size']}")
        print(f"色彩模式: {info['mode']}")
        print(f"文件格式: {info['format']}")
        print(f"数组形状: {info['array'].shape}")
    
    def get_supported_formats(self):
        """获取支持的图像格式列表"""
        return self.supported_formats
    
    def save_image(self, image_array, output_path, format=None, quality=95, embed_fingerprint=True):
        """保存图像到文件 - 嵌入数字指纹"""
        try:
            # 转换numpy数组为PIL图像
            if image_array.dtype != np.uint8:
                image_array = (image_array * 255).astype(np.uint8)
            
            pil_image = Image.fromarray(image_array)
            
            # 自动检测格式
            if format is None:
                _, ext = os.path.splitext(output_path)
                format = ext[1:].upper() if ext else 'JPEG'
            
            # 生成指纹
            fingerprint = self.generate_perceptual_hash(image_array)
            
            # 保存图像(根据格式选择是否嵌入元数据)
            if format.upper() == 'PNG' and embed_fingerprint:
                # PNG支持元数据
                metadata = PngInfo()
                metadata.add_text("Fingerprint", fingerprint)
                metadata.add_text("SaveTime", datetime.now().isoformat())
                metadata.add_text("ProcessedBy", "ImageImportProcessor")
                pil_image.save(output_path, format='PNG', pnginfo=metadata)
            elif format.upper() in ['JPEG', 'JPG']:
                # JPEG使用EXIF
                exif = pil_image.getexif()
                exif[0x9286] = f"Fingerprint:{fingerprint}"  # UserComment
                pil_image.save(output_path, format='JPEG', quality=quality, exif=exif)
            else:
                pil_image.save(output_path, format=format, quality=quality)
            
            # 保存到指纹数据库
            save_info = {
                'array': image_array,
                'path': output_path,
                'size': pil_image.size,
                'mode': pil_image.mode,
                'format': format,
                'filename': os.path.basename(output_path),
                'fingerprint': fingerprint,
                'file_size': os.path.getsize(output_path)
            }
            self.add_to_fingerprint_database(fingerprint, save_info)
            
            print(f"✓ 图像已保存: {output_path}")
            print(f"  数字指纹: {fingerprint[:32]}...")
            print(f"  文件大小: {os.path.getsize(output_path)} 字节")
            
            return True
            
        except Exception as e:
            print(f"✗ 图像保存失败: {str(e)}")
            return False
    
    def add_to_fingerprint_database(self, fingerprint, image_info):
        """添加指纹到数据库"""
        fp_id = hashlib.md5(fingerprint.encode()).hexdigest()[:16]
        
        if fp_id not in self.fingerprint_database:
            self.fingerprint_database[fp_id] = {
                'fingerprint': fingerprint,
                'original_filename': image_info['filename'],
                'first_seen': datetime.now().isoformat(),
                'locations': [],
                'count': 0
            }
        
        # 添加位置记录
        self.fingerprint_database[fp_id]['locations'].append({
            'path': image_info['path'],
            'filename': image_info['filename'],
            'timestamp': datetime.now().isoformat(),
            'size': image_info.get('file_size', 0)
        })
        self.fingerprint_database[fp_id]['count'] += 1
        
        # 自动保存
        self.save_fingerprint_database()
    
    def save_fingerprint_database(self):
        """保存指纹数据库到文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.fingerprint_database, f, indent=2, ensure_ascii=False)
            print(f"💾 数据库已保存到: {self.storage_file}")
            return True
        except Exception as e:
            print(f"✗ 保存数据库失败: {e}")
            return False
    
    def load_fingerprint_database(self):
        """从文件加载指纹数据库"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    self.fingerprint_database = json.load(f)
                print(f"✓ 已加载指纹数据库: {len(self.fingerprint_database)} 条记录")
                print(f"  文件: {self.storage_file}")
                print(f"  大小: {os.path.getsize(self.storage_file)} 字节")
            except Exception as e:
                print(f"✗ 加载数据库失败: {e}")
                print(f"  尝试备份损坏的文件...")
                try:
                    backup_file = self.storage_file + '.backup'
                    os.rename(self.storage_file, backup_file)
                    print(f"  已备份到: {backup_file}")
                except:
                    pass
                self.fingerprint_database = {}
        else:
            print(f"ℹ️  未找到历史数据库,将创建新数据库")
            print(f"  位置: {self.storage_file}")
            self.fingerprint_database = {}
    
    def display_fingerprint_database(self):
        """显示指纹数据库内容"""
        if not self.fingerprint_database:
            print("\n数据库为空")
            return
        
        print("\n" + "="*80)
        print(f"指纹数据库 - 共 {len(self.fingerprint_database)} 张不同的图片")
        print("="*80)
        
        for idx, (fp_id, fp_data) in enumerate(self.fingerprint_database.items(), 1):
            print(f"\n{idx}. 图片指纹ID: {fp_id}")
            print(f"   原始文件名: {fp_data['original_filename']}")
            print(f"   首次发现: {fp_data['first_seen']}")
            print(f"   出现次数: {fp_data['count']}")
            print(f"   保存位置:")
            for loc in fp_data['locations'][-3:]:  # 只显示最近3个
                print(f"     - {loc['path']} ({loc['timestamp'][:10]})")
    
    def select_image_with_dialog(self):
        """使用图形化对话框选择图像文件"""
        root = Tk()
        root.withdraw()  # 隐藏主窗口
        root.attributes('-topmost', True)  # 窗口置顶
        
        print("\n正在打开文件选择对话框...")
        
        # 构建文件类型过滤器
        file_types = [
            ("图像文件", "*.jpg *.jpeg *.png *.bmp *.tiff *.webp"),
            ("JPEG图像", "*.jpg *.jpeg"),
            ("PNG图像", "*.png"),
            ("BMP图像", "*.bmp"),
            ("所有文件", "*.*")
        ]
        
        file_path = filedialog.askopenfilename(
            title="选择图像文件",
            filetypes=file_types,
            initialdir=os.path.expanduser("~")
        )
        
        root.destroy()  # 销毁根窗口
        
        if not file_path:
            print("未选择文件")
            return None, None
        
        try:
            image_hash, image_info = self.load_image_from_path(file_path)
            return image_hash, image_info
        except Exception as e:
            print(f"✗ 加载失败: {str(e)}")
            return None, None
    
    def interactive_load_image(self):
        """交互式加载图像"""
        print("\n" + "="*60)
        print("图像导入")
        print("="*60)
        print(f"支持的格式: {', '.join(self.supported_formats)}")
        
        while True:
            print("\n请选择导入方式:")
            print("1. 图形化选择文件 (推荐)")
            print("2. 手动输入文件路径")
            print("q. 退出")
            
            choice = input("\n请输入选项 (1/2/q): ").strip().lower()
            
            if choice == 'q':
                return None, None
            
            elif choice == '1':
                # 使用图形化对话框
                image_hash, image_info = self.select_image_with_dialog()
                if image_hash:
                    self.display_image_info(image_hash)
                    return image_hash, image_info
                else:
                    retry = input("\n是否重试? (y/n): ").strip().lower()
                    if retry != 'y':
                        return None, None
            
            elif choice == '2':
                # 手动输入路径
                file_path = input("\n请输入图像文件路径 (或输入 'q' 返回): ").strip()
                
                if file_path.lower() == 'q':
                    continue
                
                # 移除可能的引号
                file_path = file_path.strip('"').strip("'")
                
                try:
                    image_hash, image_info = self.load_image_from_path(file_path)
                    self.display_image_info(image_hash)
                    return image_hash, image_info
                except Exception as e:
                    print(f"✗ 错误: {str(e)}")
                    retry = input("是否重试? (y/n): ").strip().lower()
                    if retry != 'y':
                        return None, None
            else:
                print("✗ 无效选项,请重新选择")
    
    def list_loaded_images(self):
        """列出所有已加载的图像 - 增强版"""
        if not self.loaded_images:
            print("\n当前会话没有已加载的图像")
            return
        
        print("\n当前会话已加载的图像:")
        print("-" * 80)
        for idx, (hash_key, info) in enumerate(self.loaded_images.items(), 1):
            fp_short = info.get('fingerprint', 'N/A')[:16]
            print(f"{idx}. [{hash_key[:16]}...] {info['filename']}")
            print(f"    尺寸: {info['size'][0]}x{info['size'][1]} | 指纹: {fp_short}...")
    
# 测试用例
def test_image_import():
    """测试图像导入功能"""
    processor = ImageImportProcessor()
    
    print("支持的图像格式:", processor.get_supported_formats())
    
    # 测试从文件导入（这里使用一个示例，实际使用时需要替换为真实路径）
    try:
        # 创建一个测试图像
        test_image = Image.new('RGB', (100, 100), color='red')
        test_path = 'test_image.jpg'
        test_image.save(test_path)
        
        # 导入测试图像
        image_hash, info = processor.load_image_from_path(test_path)
        print("\n=== 文件导入测试 ===")
        processor.display_image_info(image_hash)
        
        # 清理测试文件
        os.remove(test_path)
        
    except Exception as e:
        print(f"文件导入测试失败: {e}")
    
    # 测试从字节数据导入
    try:
        # 创建测试图像并转换为字节
        test_image = Image.new('RGB', (50, 50), color='blue')
        import io
        img_byte_arr = io.BytesIO()
        test_image.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        
        # 导入字节数据
        image_hash, info = processor.load_image_from_bytes(img_byte_arr)
        print("\n=== 字节导入测试 ===")
        processor.display_image_info(image_hash)
        
    except Exception as e:
        print(f"字节导入测试失败: {e}")

# 使用示例
def usage_example():
    """使用示例 - 带持续交互菜单"""
    print("="*60)
    print("ImageImportProcessor - 数字指纹版")
    print("="*60)
    
    processor = ImageImportProcessor()
    
    while True:
        print("\n" + "="*60)
        print("主菜单")
        print("="*60)
        print("1. 图形化选择文件并加载图像")
        print("2. 手动输入路径加载图像")
        print("3. 查看当前会话已加载的图像")
        print("4. 查看指定图像的详细信息")
        print("5. 保存图像到文件(嵌入数字指纹)")
        print("6. 查看指纹数据库(所有历史记录)")
        print("7. 显示使用示例代码")
        print("8. 清空指纹数据库")
        print("9. 显示数据库文件位置")
        print("q. 退出程序")
        
        choice = input("\n请输入选项: ").strip().lower()
        
        if choice == 'q':
            print("\n✓ 数据已自动保存")
            print("感谢使用,再见!")
            break
        
        elif choice == '1':
            print("\n【图形化选择文件】")
            image_hash, image_info = processor.select_image_with_dialog()
            if image_hash:
                print(f"\n✓ 成功加载: {image_info['filename']}")
                print(f"  图像哈希: {image_hash}")
                print(f"  数组形状: {image_info['array'].shape}")
        
        elif choice == '2':
            file_path = input("\n请输入图像文件路径: ").strip().strip('"').strip("'")
            try:
                image_hash, image_info = processor.load_image_from_path(file_path)
                print(f"\n✓ 成功加载: {image_info['filename']}")
            except Exception as e:
                print(f"\n✗ 加载失败: {str(e)}")
        
        elif choice == '3':
            processor.list_loaded_images()
        
        elif choice == '4':
            processor.list_loaded_images()
            if processor.loaded_images:
                hash_input = input("\n请输入图像哈希的前几位: ").strip()
                matched = [h for h in processor.loaded_images.keys() if h.startswith(hash_input)]
                if matched:
                    processor.display_image_info(matched[0])
                else:
                    print("✗ 未找到匹配的图像")
        
        elif choice == '5':
            processor.list_loaded_images()
            if processor.loaded_images:
                hash_input = input("\n请输入要保存的图像哈希的前几位: ").strip()
                matched = [h for h in processor.loaded_images.keys() if h.startswith(hash_input)]
                
                if matched:
                    output_path = input("请输入保存路径 (如: output.png): ").strip()
                    image_info = processor.get_image_info(matched[0])
                    processor.save_image(image_info['array'], output_path)
                else:
                    print("✗ 未找到匹配的图像")
        
        elif choice == '6':
            processor.display_fingerprint_database()
        
        elif choice == '7':
            print("\n" + "="*60)
            print("代码使用示例")
            print("="*60)
            print("""
# 创建处理器(自动加载历史记录)
from image_input import ImageImportProcessor

processor = ImageImportProcessor()

# 加载图片(自动识别是否为已知图片)
image_hash, image_info = processor.select_image_with_dialog()

if image_hash:
    # 获取图像数组和指纹
    img_array = image_info['array']
    fingerprint = image_info['fingerprint']
    print(f"数字指纹: {fingerprint}")
    
    # 保存图片(自动嵌入指纹)
    processor.save_image(img_array, 'output.png')
    
    # 再次加载保存的图片,会自动识别出是同一张
    processor.load_image_from_path('output.png')

# 查看指纹数据库
processor.display_fingerprint_database()
            """)
        
        elif choice == '8':
            confirm = input("\n⚠️  确认清空指纹数据库? (yes/no): ").strip().lower()
            if confirm == 'yes':
                processor.fingerprint_database = {}
                processor.save_fingerprint_database()
                print("✓ 数据库已清空")
            else:
                print("✗ 操作已取消")
        
        elif choice == '9':
            print(f"\n📂 数据库文件信息:")
            print(f"  路径: {processor.storage_file}")
            if os.path.exists(processor.storage_file):
                print(f"  状态: ✓ 文件存在")
                print(f"  大小: {os.path.getsize(processor.storage_file)} 字节")
                print(f"  记录数: {len(processor.fingerprint_database)}")
                print(f"  最后修改: {datetime.fromtimestamp(os.path.getmtime(processor.storage_file))}")
            else:
                print(f"  状态: ✗ 文件不存在 (将在保存时自动创建)")
        
        else:
            print("\n✗ 无效选项,请重新选择")

if __name__ == "__main__":
    # test_image_import()  # 原有的测试
    usage_example()  # 交互式示例
