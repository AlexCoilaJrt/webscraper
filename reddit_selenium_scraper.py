"""
Reddit Selenium Scraper (Fallback)
PROYECTO ACADÉMICO - Solo para fines educativos

Este scraper usa Selenium para extraer datos de Reddit cuando la API no está disponible.
Usa old.reddit.com para facilitar el scraping.
"""

import time
import random
import re
import logging
from typing import List, Dict, Optional
from datetime import datetime
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

# Intentar importar undetected-chromedriver
try:
    import undetected_chromedriver as uc
    UC_AVAILABLE = True
except ImportError:
    UC_AVAILABLE = False


class RedditSeleniumScraper:
    """
    Scraper de Reddit usando Selenium (Fallback cuando API no está disponible)
    
    IMPORTANTE: Este código es solo para fines académicos y educativos.
    Respeta los términos de servicio de Reddit y las leyes locales.
    """
    
    def __init__(self, headless: bool = True):
        """
        Inicializar el scraper de Reddit con Selenium
        
        Args:
            headless: Si True, ejecuta el navegador en modo headless
        """
        self.headless = headless
        self.driver = None
        self._setup_driver()
    
    def _setup_driver(self):
        """Configurar el driver de Chrome con opciones anti-detección"""
        try:
            if UC_AVAILABLE:
                options = uc.ChromeOptions()
                if self.headless:
                    options.add_argument('--headless=new')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option('useAutomationExtension', False)
                
                self.driver = uc.Chrome(options=options)
                logger.info("✅ Driver de Reddit configurado (undetected-chromedriver)")
            else:
                options = ChromeOptions()
                if self.headless:
                    options.add_argument('--headless=new')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option('useAutomationExtension', False)
                
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
                logger.info("✅ Driver de Reddit configurado (Selenium estándar)")
            
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
        except Exception as e:
            logger.error(f"❌ Error configurando driver: {e}")
            raise
    
    def _parse_score(self, score_text: str) -> int:
        """Parsear score de Reddit (ej: '1.2k' -> 1200)"""
        try:
            if not score_text or score_text.strip() == '':
                return 0
            
            score_text = score_text.strip().lower()
            
            # Remover caracteres no numéricos excepto k, m, .
            score_text = re.sub(r'[^\d.km]', '', score_text)
            
            if 'k' in score_text:
                number = float(score_text.replace('k', ''))
                return int(number * 1000)
            elif 'm' in score_text:
                number = float(score_text.replace('m', ''))
                return int(number * 1000000)
            else:
                return int(float(score_text))
        except:
            return 0
    
    def _parse_comments(self, comments_text: str) -> int:
        """Parsear número de comentarios"""
        try:
            if not comments_text:
                return 0
            
            # Extraer número de comentarios
            match = re.search(r'(\d+[km]?)\s*comment', comments_text.lower())
            if match:
                return self._parse_score(match.group(1))
            
            # Si no hay match, intentar extraer número directo
            numbers = re.findall(r'\d+', comments_text)
            if numbers:
                return int(numbers[0])
            
            return 0
        except:
            return 0
    
    def scrape_subreddit(self, subreddit_name: str, max_posts: int = 100, sort: str = 'hot') -> List[Dict]:
        """
        Scrapear posts de un subreddit usando old.reddit.com
        
        Args:
            subreddit_name: Nombre del subreddit
            max_posts: Número máximo de posts
            sort: Orden ('hot', 'new', 'top')
        
        Returns:
            Lista de diccionarios con datos de los posts
        """
        posts = []
        
        try:
            # Usar old.reddit.com para más facilidad
            if sort == 'hot':
                url = f"https://old.reddit.com/r/{subreddit_name}/"
            elif sort == 'new':
                url = f"https://old.reddit.com/r/{subreddit_name}/new/"
            elif sort == 'top':
                url = f"https://old.reddit.com/r/{subreddit_name}/top/"
            else:
                url = f"https://old.reddit.com/r/{subreddit_name}/"
            
            logger.info(f"🌐 Navegando a: {url}")
            self.driver.get(url)
            time.sleep(3)
            
            scrolls = 0
            max_scrolls = 50
            posts_ids_vistos = set()
            
            while len(posts) < max_posts and scrolls < max_scrolls:
                # Buscar posts visibles
                post_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div.thing')
                logger.info(f"📊 Posts encontrados en página: {len(post_elements)}")
                
                for post_elem in post_elements:
                    try:
                        # Obtener ID único del post
                        post_id = post_elem.get_attribute('data-fullname') or post_elem.get_attribute('data-permalink')
                        if not post_id:
                            post_id = post_elem.get_attribute('id') or f"post_{len(posts)}"
                        
                        if post_id in posts_ids_vistos:
                            continue
                        
                        posts_ids_vistos.add(post_id)
                        
                        # Extraer título - MEJORADO (múltiples selectores)
                        title = ""
                        post_url = ""
                        try:
                            # Método 1: p.title > a.title (más común en old.reddit)
                            title_elem = post_elem.find_element(By.CSS_SELECTOR, 'p.title > a.title')
                            title = title_elem.text.strip()
                            post_url = title_elem.get_attribute('href')
                        except:
                            try:
                                # Método 2: a.title (sin p.title)
                                title_elem = post_elem.find_element(By.CSS_SELECTOR, 'a.title')
                                title = title_elem.text.strip()
                                post_url = title_elem.get_attribute('href')
                            except:
                                try:
                                    # Método 3: Buscar cualquier enlace con texto largo
                                    links = post_elem.find_elements(By.TAG_NAME, 'a')
                                    for link in links:
                                        link_text = link.text.strip()
                                        if len(link_text) > 10 and link.get_attribute('href'):
                                            title = link_text
                                            post_url = link.get_attribute('href')
                                            break
                                except:
                                    title = "Sin título"
                        
                        if not title:
                            title = "Sin título"
                        
                        # Extraer autor - MEJORADO (múltiples métodos)
                        author = "Unknown"
                        try:
                            # Método 1: a.author (más común)
                            author_elem = post_elem.find_element(By.CSS_SELECTOR, 'a.author')
                            author = author_elem.text.strip()
                        except:
                            try:
                                # Método 2: Buscar en p.tagline
                                tagline = post_elem.find_element(By.CSS_SELECTOR, 'p.tagline')
                                author_link = tagline.find_element(By.CSS_SELECTOR, 'a')
                                author = author_link.text.strip()
                            except:
                                try:
                                    # Método 3: Buscar cualquier link con class que contenga "author"
                                    author_links = post_elem.find_elements(By.CSS_SELECTOR, 'a[class*="author"]')
                                    if author_links:
                                        author = author_links[0].text.strip()
                                except:
                                    author = "Unknown"
                        
                        # Extraer score - MEJORADO
                        score = 0
                        try:
                            # Método 1: div.score.unvoted o div.score.likes
                            score_elem = post_elem.find_element(By.CSS_SELECTOR, 'div.score.unvoted, div.score.likes, div.score')
                            score_text = score_elem.text.strip()
                            score = self._parse_score(score_text)
                        except:
                            try:
                                # Método 2: Buscar en spans con números
                                score_spans = post_elem.find_elements(By.CSS_SELECTOR, 'span.score')
                                if score_spans:
                                    score_text = score_spans[0].text.strip()
                                    score = self._parse_score(score_text)
                            except:
                                score = 0
                        
                        # Extraer comentarios - MEJORADO
                        num_comments = 0
                        try:
                            # Método 1: a.comments (más común)
                            comments_elem = post_elem.find_element(By.CSS_SELECTOR, 'a.comments')
                            comments_text = comments_elem.text.strip()
                            num_comments = self._parse_comments(comments_text)
                        except:
                            try:
                                # Método 2: Buscar texto que contenga "comment"
                                all_text = post_elem.text.lower()
                                comment_match = re.search(r'(\d+[km]?)\s*comment', all_text)
                                if comment_match:
                                    num_comments = self._parse_score(comment_match.group(1))
                            except:
                                num_comments = 0
                        
                        # Extraer fecha
                        try:
                            time_elem = post_elem.find_element(By.CSS_SELECTOR, 'time.live-timestamp')
                            created_at = time_elem.get_attribute('datetime') or datetime.now().isoformat()
                        except:
                            created_at = datetime.now().isoformat()
                        
                        # Extraer permalink
                        try:
                            permalink_elem = post_elem.find_element(By.CSS_SELECTOR, 'a.title')
                            permalink = permalink_elem.get_attribute('href')
                            if permalink and not permalink.startswith('http'):
                                permalink = f"https://old.reddit.com{permalink}"
                        except:
                            permalink = post_url or ""
                        
                        # Extraer imagen (si es un post de imagen)
                        image_url = None
                        try:
                            thumbnail = post_elem.find_element(By.CSS_SELECTOR, 'a.thumbnail img')
                            img_src = thumbnail.get_attribute('src')
                            if img_src and 'default' not in img_src.lower():
                                # Intentar obtener imagen de alta resolución
                                if 'thumbs.redditmedia.com' in img_src:
                                    # Reddit usa thumbnails, intentar obtener imagen original
                                    image_url = img_src.replace('_b.jpg', '.jpg').replace('_thumb', '')
                                else:
                                    image_url = img_src
                        except:
                            pass
                        
                        # Verificar si el post URL es una imagen
                        if not image_url and post_url:
                            if post_url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                                image_url = post_url
                        
                        # Extraer contenido (texto del post) - MEJORADO
                        content = ""
                        try:
                            # Método 1: div.usertext-body (contenido del post)
                            text_elem = post_elem.find_element(By.CSS_SELECTOR, 'div.usertext-body')
                            content = text_elem.text.strip()
                            # Si el contenido es muy corto o parece ser metadata, buscar en otro lugar
                            if len(content) < 20:
                                raise Exception("Contenido muy corto")
                        except:
                            try:
                                # Método 2: div.md (contenido markdown)
                                md_elem = post_elem.find_element(By.CSS_SELECTOR, 'div.md')
                                content = md_elem.text.strip()
                            except:
                                try:
                                    # Método 3: Buscar cualquier div con texto largo que no sea título
                                    divs = post_elem.find_elements(By.TAG_NAME, 'div')
                                    for div in divs:
                                        div_text = div.text.strip()
                                        # Excluir elementos que parecen ser metadata o botones
                                        if (len(div_text) > 50 and 
                                            'k miembros' not in div_text.lower() and
                                            'en línea' not in div_text.lower() and
                                            'hace' not in div_text.lower() and
                                            div_text != title):
                                            content = div_text
                                            break
                                except:
                                    # Si no hay contenido, usar título como contenido
                                    content = title
                        
                        # Limpiar contenido: remover metadata del subreddit que puede aparecer
                        # Patrones comunes de metadata que se confunden con contenido
                        metadata_patterns = [
                            r'Un subreddit para.*?\.',
                            r'\d+\s*k\s*Miembros',
                            r'\d+\s*En línea',
                            r'hace\s+\d+\s*[a-z]',
                            r'\d+\s*votos',
                            r'\d+\s*comentarios',
                        ]
                        for pattern in metadata_patterns:
                            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
                        content = content.strip()
                        
                        # Si después de limpiar el contenido es muy corto, usar título
                        if len(content) < 10:
                            content = title
                        
                        # Extraer subreddit - MEJORADO (evitar duplicación)
                        subreddit = subreddit_name
                        try:
                            # Método 1: a.subreddit
                            subreddit_elem = post_elem.find_element(By.CSS_SELECTOR, 'a.subreddit')
                            subreddit_text = subreddit_elem.text.strip()
                            # Limpiar formato "r/subreddit" o solo "subreddit"
                            if subreddit_text.startswith('r/'):
                                subreddit = subreddit_text.replace('r/', '').strip()
                            else:
                                subreddit = subreddit_text
                        except:
                            try:
                                # Método 2: Buscar en p.tagline
                                tagline = post_elem.find_element(By.CSS_SELECTOR, 'p.tagline')
                                subreddit_links = tagline.find_elements(By.CSS_SELECTOR, 'a')
                                for link in subreddit_links:
                                    link_text = link.text.strip()
                                    href = link.get_attribute('href') or ''
                                    if link_text.startswith('r/') or 'subreddit' in href.lower():
                                        if link_text.startswith('r/'):
                                            subreddit = link_text.replace('r/', '').strip()
                                        else:
                                            subreddit = link_text
                                        break
                            except:
                                subreddit = subreddit_name
                        
                        # Asegurar que no se duplique (ej: "r/PERU r/PERU" -> "PERU")
                        if 'r/' in subreddit:
                            subreddit = subreddit.replace('r/', '').strip()
                        # Remover duplicados si existen
                        words = subreddit.split()
                        if len(words) > 1 and words[0] == words[1]:
                            subreddit = words[0]
                        
                        post_data = {
                            'id': post_id,
                            'platform': 'reddit',
                            'title': title,
                            'content': content,
                            'author': author,
                            'subreddit': subreddit,  # Usar subreddit extraído (sin duplicar)
                            'score': score,
                            'upvotes': score,  # En old.reddit no se diferencia fácilmente
                            'downvotes': 0,
                            'comments': num_comments,
                            'url': post_url,
                            'permalink': permalink,
                            'created_at': created_at,
                            'flair': None,  # old.reddit usa diferentes selectores
                            'image_url': image_url,
                            'scraped_at': datetime.now().isoformat()
                        }
                        
                        posts.append(post_data)
                        logger.info(f"✅ Post extraído: {title[:50]}... (Score: {score}, Comments: {num_comments})")
                        
                        if len(posts) >= max_posts:
                            break
                            
                    except Exception as e:
                        logger.warning(f"⚠️ Error extrayendo post individual: {e}")
                        continue
                
                if len(posts) >= max_posts:
                    break
                
                # Scroll para cargar más posts
                logger.info(f"📜 Scroll {scrolls + 1}/{max_scrolls} para cargar más posts...")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                scrolls += 1
            
            logger.info(f"✅ Extraídos {len(posts)} posts de r/{subreddit_name}")
            return posts
        except Exception as e:
            logger.error(f"❌ Error scrapeando r/{subreddit_name}: {e}")
            return []

    def search_posts(self, query: str, max_posts: int = 100, subreddit: Optional[str] = None) -> List[Dict]:
        """Buscar posts en Reddit usando old.reddit.com"""
        posts: List[Dict] = []
        seen_ids = set()

        if not query:
            return posts

        try:
            search_query = quote(query, safe=' ')
            search_query = search_query.replace(' ', '+')

            if subreddit:
                search_url = f"https://old.reddit.com/r/{subreddit}/search/?q={search_query}&restrict_sr=on&sort=new"
            else:
                search_url = f"https://old.reddit.com/search/?q={search_query}&sort=new"

            logger.info(f"🌐 Buscando en Reddit con Selenium: {search_url}")
            self.driver.get(search_url)
            time.sleep(3)

            scrolls = 0
            max_scrolls = 40

            while len(posts) < max_posts and scrolls < max_scrolls:
                result_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div.search-result')
                logger.debug(f"🔍 Resultados visibles en búsqueda: {len(result_elements)}")

                for result_elem in result_elements:
                    if len(posts) >= max_posts:
                        break

                    try:
                        post_id = result_elem.get_attribute('data-fullname') or result_elem.get_attribute('data-permalink')
                        if not post_id:
                            post_id = result_elem.get_attribute('id') or f"search_{len(posts)}_{scrolls}"

                        if post_id in seen_ids:
                            continue

                        seen_ids.add(post_id)

                        # Título y URL
                        title = ""
                        post_url = ""
                        try:
                            title_elem = result_elem.find_element(By.CSS_SELECTOR, 'a.search-title')
                            title = title_elem.text.strip()
                            post_url = title_elem.get_attribute('href')
                        except Exception:
                            title = "Sin título"

                        # Subreddit del resultado
                        subreddit_name = subreddit or ""
                        try:
                            subreddit_elem = result_elem.find_element(By.CSS_SELECTOR, 'a.search-subreddit-link')
                            subreddit_text = subreddit_elem.text.strip()
                            if subreddit_text.startswith('r/'):
                                subreddit_name = subreddit_text.replace('r/', '').strip()
                            else:
                                subreddit_name = subreddit_text
                        except Exception:
                            subreddit_name = subreddit_name or ""

                        # Autor
                        author = "Unknown"
                        try:
                            author_elem = result_elem.find_element(By.CSS_SELECTOR, 'a.search-author')
                            author = author_elem.text.strip()
                        except Exception:
                            pass

                        # Score y comentarios
                        score = 0
                        try:
                            score_elem = result_elem.find_element(By.CSS_SELECTOR, 'span.search-score')
                            score = self._parse_score(score_elem.text)
                        except Exception:
                            pass

                        num_comments = 0
                        try:
                            comments_elem = result_elem.find_element(By.CSS_SELECTOR, 'a.search-comments')
                            num_comments = self._parse_comments(comments_elem.text)
                        except Exception:
                            pass

                        # Fecha
                        created_at = datetime.now().isoformat()
                        try:
                            time_elem = result_elem.find_element(By.CSS_SELECTOR, 'time')
                            created_at = time_elem.get_attribute('datetime') or time_elem.get_attribute('title') or created_at
                        except Exception:
                            pass

                        # Imagen
                        image_url = None
                        try:
                            thumb = result_elem.find_element(By.CSS_SELECTOR, 'a.thumbnail img')
                            img_src = thumb.get_attribute('src')
                            if img_src and 'default' not in img_src.lower():
                                if 'thumbs.redditmedia.com' in img_src:
                                    image_url = img_src.replace('_b.jpg', '.jpg').replace('_thumb', '')
                                else:
                                    image_url = img_src
                        except Exception:
                            pass

                        # Contenido/snippet
                        content = title
                        try:
                            content_elem = result_elem.find_element(By.CSS_SELECTOR, 'div.search-result-content')
                            snippet = content_elem.text.strip()
                            if snippet:
                                content = snippet
                        except Exception:
                            pass

                        # Evitar contenido muy corto
                        if not content or len(content.strip()) < 5:
                            content = title

                        posts.append({
                            'id': post_id,
                            'platform': 'reddit',
                            'title': title,
                            'content': content,
                            'author': author,
                            'subreddit': subreddit_name or 'all',
                            'score': score,
                            'upvotes': score,
                            'downvotes': 0,
                            'comments': num_comments,
                            'url': post_url,
                            'permalink': post_url,
                            'created_at': created_at,
                            'image_url': image_url,
                            'scraped_at': datetime.now().isoformat()
                        })

                    except Exception as e:
                        logger.debug(f"⚠️ Error procesando resultado de búsqueda: {e}")
                        continue

                if len(posts) >= max_posts:
                    break

                # Scroll para cargar más resultados
                scrolls += 1
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2, 3))

            return posts

        except Exception as e:
            logger.error(f"❌ Error buscando posts en Reddit con Selenium: {e}")
            return posts
    
    def close(self):
        """Cerrar el driver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("✅ Driver de Reddit cerrado")
            except:
                pass

