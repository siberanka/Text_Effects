<!-- DOWNLOAD_BADGES_START -->
<p align="center">
  <a href="https://gitlab.com/siberanka/Text_Effects/-/releases/permalink/latest/downloads/package.zip"><img alt="Download Resource Pack" src="https://img.shields.io/badge/Download-Resource%20Pack-8e44ad?logo=gitlab&logoColor=white"></a>
</p>
<!-- DOWNLOAD_BADGES_END -->

# Text Effects — siberanka Gradient Edition

Minecraft Java Edition metinlerine renk koduyla tetiklenen shader efektleri ekleyen, [TheSalt's Text Effects](https://github.com/TheSalts/Text_Effects) tabanlı kaynak paketi. Bu fork mevcut efektleri korur ve rütbe/etiket kullanımı için 16 statik, 16 sağdan sola akan koyu-açık gradyan içerir.

> [!IMPORTANT]
> Paket `rendertype_text` çekirdek shader'ını değiştirir. Aynı shader'ı değiştiren başka bir kaynak paketiyle birlikte kullanılamaz; kaynak paketi listesinde üstte olan paket diğerini ezer.

> [!WARNING]
> Mojang, kaynak paketlerinden çekirdek shader değiştirmeyi resmî olarak desteklenen bir genişletme noktası saymıyor. Bu fork sürüm kırılmalarını overlay'lerle yönetir; gelecekteki Minecraft sürümleri yeni bir overlay gerektirebilir.

## Nasıl çalışır?

Minecraft metninde kullanılan tam RGB değeri `assets/minecraft/shaders/include/_config.glsl` içindeki bir tetikleyiciyle eşleştiğinde ilgili efekt uygulanır. Tetikleyici rengi ekranda görünmek zorunda değildir; efekt kendi görünür rengini veya gradyanını üretir.

Sunucu, harita, `/tellraw`, `/title`, takım prefix'i, `text_display` ve eklenti örnekleri için [wiki.md](./wiki.md) dosyasına bakın. Efekt fonksiyonlarının ayrıntılı API açıklaması [CONFIGURATION.md](./CONFIGURATION.md) içindedir.

## Sürüm uyumluluğu

Tek ZIP, Minecraft Java Edition kaynak paketi formatı 7–97.1 aralığını bildirir. Upstream'in çok sürümlü düzeni korunmuştur; test edilmemiş sonraki formatlar destek kapsamında değildir:

| Minecraft ailesi | Kaynak formatı | Kullanılan paket katmanı |
| --- | ---: | --- |
| 1.17.x–1.21.1 | 7–34 | Ana `assets/` ağacı |
| 1.21.2–1.21.5 | 35–55 | Ana ağaç + `1_21_2` overlay |
| 1.21.6–1.21.11 | 63–75 | Ana ağaç + `1_21_6` overlay |
| 26.1–26.1.1 | 76–84 | Öncekiler + `26_1` overlay |
| 26.2 | 88–96 | Öncekiler + `26_2` overlay |
| 26.3 | 97.1 | Öncekiler + `26_3` overlay |

1.20.2 öncesi istemciler `supported_formats` alanını tanımadığı için paketi uyumsuz işaretleyebilir; bu, tek ZIP ile eski ve yeni metadata biçimlerini aynı anda taşımanın doğal sonucudur. Paket yine de “Evet” seçilerek yüklenir. Sunucu dağıtımında istemci paketi doğrudan uygular.

## Statik rütbe gradyanları

Her gradyanda ilk renk koyu temel, ikinci renk daha açık tamamlayıcıdır. Yön yukarıdan aşağıya `4.0` olarak sabittir. Tetikleyiciler ve otomatik gölge renkleri birbirleriyle çakışmaması için dördün katlarından seçilmiştir.

| Gradyan | Kullanılacak tetikleyici | Otomatik gölge | Görünen koyu → açık renk |
| --- | --- | --- | --- |
| Gri → Beyaz | `#F8F8DC` | `#3E3E37` | `#606060` → `#FFFFFF` |
| Sarı → Açık sarı | `#F8F8E0` | `#3E3E38` | `#CC9C00` → `#FFF480` |
| Turuncu → Açık turuncu | `#F8F8E4` | `#3E3E39` | `#B84800` → `#FFB45C` |
| Mavi → Camgöbeği | `#F8F8E8` | `#3E3E3A` | `#1860B8` → `#40E0FF` |
| Lacivert → Açık lacivert | `#F8F8EC` | `#3E3E3B` | `#0C2070` → `#4060C0` |
| Kırmızı → Açık kırmızı | `#F8F8F0` | `#3E3E3C` | `#981818` → `#FF6868` |
| Yeşil → Açık yeşil | `#F8F8F4` | `#3E3E3D` | `#147034` → `#60E084` |
| Mor → Açık mor | `#F8F8F8` | `#3E3E3E` | `#501C80` → `#B070E8` |
| Pembe → Açık pembe | `#F8F8FC` | `#3E3E3F` | `#983064` → `#FF90C4` |
| Koyu gri → Gri | `#F8FCDC` | `#3E3F37` | `#242424` → `#808080` |
| Siyah → Füme | `#F8FCE0` | `#3E3F38` | `#080808` → `#484848` |
| Koyu yeşil → Yeşil | `#F8FCE4` | `#3E3F39` | `#084018` → `#34984C` |
| Koyu turkuaz → Turkuaz | `#F8FCE8` | `#3E3F3A` | `#005854` → `#48C8C0` |
| Camgöbeği → Açık camgöbeği | `#F8FCEC` | `#3E3F3B` | `#007088` → `#70ECF8` |
| Eflatun → Açık eflatun | `#F8FCF0` | `#3E3F3C` | `#701868` → `#E870DC` |
| Kahverengi → Açık kahverengi | `#F8FCF4` | `#3E3F3D` | `#5C3418` → `#BC7C4C` |

## Sağdan sola akan rütbe efektleri

Bu kodlar aynı koyu-açık paletleri RGB/rainbow efekti gibi sürekli hareket ettirir. Görsel akış sağdan sola; shader'ın pozitif X fazı `direction=2.0`, hız `500.0` değeridir. İlk renk her zaman koyu kaynak renktir.

| Akan efekt | Yeni tetikleyici | Otomatik gölge | Görünen koyu ↔ açık renk |
| --- | --- | --- | --- |
| Gri ↔ Beyaz | `#F8FCF8` | `#3E3F3E` | `#606060` ↔ `#FFFFFF` |
| Sarı ↔ Açık sarı | `#F8FCFC` | `#3E3F3F` | `#CC9C00` ↔ `#FFF480` |
| Turuncu ↔ Açık turuncu | `#FCF8DC` | `#3F3E37` | `#B84800` ↔ `#FFB45C` |
| Mavi ↔ Camgöbeği | `#FCF8E0` | `#3F3E38` | `#1860B8` ↔ `#40E0FF` |
| Lacivert ↔ Açık lacivert | `#FCF8E4` | `#3F3E39` | `#0C2070` ↔ `#4060C0` |
| Kırmızı ↔ Açık kırmızı | `#FCF8E8` | `#3F3E3A` | `#981818` ↔ `#FF6868` |
| Yeşil ↔ Açık yeşil | `#FCF8EC` | `#3F3E3B` | `#147034` ↔ `#60E084` |
| Mor ↔ Açık mor | `#FCF8F0` | `#3F3E3C` | `#501C80` ↔ `#B070E8` |
| Pembe ↔ Açık pembe | `#FCF8F4` | `#3F3E3D` | `#983064` ↔ `#FF90C4` |
| Koyu gri ↔ Gri | `#FCF8F8` | `#3F3E3E` | `#242424` ↔ `#808080` |
| Siyah ↔ Füme | `#FCF8FC` | `#3F3E3F` | `#080808` ↔ `#484848` |
| Koyu yeşil ↔ Yeşil | `#FCFCDC` | `#3F3F37` | `#084018` ↔ `#34984C` |
| Koyu turkuaz ↔ Turkuaz | `#FCFCE0` | `#3F3F38` | `#005854` ↔ `#48C8C0` |
| Camgöbeği ↔ Açık camgöbeği | `#FCFCE4` | `#3F3F39` | `#007088` ↔ `#70ECF8` |
| Eflatun ↔ Açık eflatun | `#FCFCE8` | `#3F3F3A` | `#701868` ↔ `#E870DC` |
| Kahverengi ↔ Açık kahverengi | `#FCFCEC` | `#3F3F3B` | `#5C3418` ↔ `#BC7C4C` |

Kısa örnek:

```mcfunction
tellraw @a {"text":"[ADMIN]","color":"#F8F8F0","bold":true}
title @a title {"text":"VIP","color":"#F8F8E0","bold":true}
title @a actionbar {"text":"AKAN MAVI","color":"#FCF8E0","bold":true}
```

## Kaynak paketteki tüm tetikleyici renk kodları

Aşağıdaki liste `_config.glsl` içindeki 67 tetikleyicinin tamamıdır. “Gölge” sütunu efektin Minecraft'ın metin gölgesine de uygulandığını gösterir.

| Kod | Efekt | Görünür renk/renkler | Gölge |
| --- | --- | --- | :---: |
| `#F8F854` | Shake | `#FF5050` | Evet |
| `#F8F858` | Wavy | `#50FF50` | Evet |
| `#F8F85C` | Rainbow | Dinamik gökkuşağı | Hayır |
| `#F8F860` | Bouncy | `#FFAA00` | Evet |
| `#F8F864` | Blinking | `#5050FF` | Evet |
| `#F8F868` | Pulse | `#50FFFF` | Evet |
| `#F8F86C` | Spin | `#FF50FF` | Evet |
| `#F8F870` | Sequential Spin | `#FFFFFF` | Evet |
| `#F8F874` | Fade | `#FFFF50` | Evet |
| `#F8F878` | Iterating Jump | `#AA00FF` | Evet |
| `#F8F87C` | Glitch | `#FF5050` | Evet |
| `#F8F880` | Scale ×1.5 | `#50FFFF` | Evet |
| `#F8F884` | Offset Up | `#FFAA00` | Evet |
| `#F8F888` | Static Gradient | `#00C800` → `#FFFF00` | Hayır |
| `#F8F88C` | Dynamic Gradient | `#FF0000` ↔ `#0000FF` | Hayır |
| `#F8F890` | Dynamic Gradient | `#00C800` ↔ `#FFFF00` | Hayır |
| `#F8F894` | Lava | `#FF1400` ↔ `#FFC800` | Hayır |
| `#F8F898` | Wavy + Rainbow | Dinamik gökkuşağı | Hayır |
| `#F8F89C` | Bouncy + Rainbow | Dinamik gökkuşağı | Hayır |
| `#C86432` | Fast Shake | `#FFFF55` | Hayır |
| `#FFC8C8` | Shadow Support / Wavy | Tetikleyici rengi | Evet |
| `#F8F8A0` | Aurora | `#FF4DB3` ↔ `#4DFF99` ↔ `#6699FF` | Hayır |
| `#F8F8A4` | Split | `#FF64C8` | Evet |
| `#F8F8AC` | Outline | Gövde `#FFFFFF`, çizgi `#000000` | Hayır |
| `#F8F8B0` | Hatch | Gövde `#A5E926`, tarama `#FFFFFF` | Hayır |
| `#F8F8B4` | Neon | Işıma `#50DCFF` | Hayır |
| `#F8F8B8` | RGBA Alpha | `#FF5050`, %50 alfa | Hayır |
| `#F8F8BC` | Chromatic Aberration | Gövde `#FFFFFF`, RGB saçılması | Hayır |
| `#F8F8C0` | 3D Extrude | Gövde `#FFC800`, otomatik koyulaşma | Hayır |
| `#F8F8CC` | 3D Extrude 2-color | `#FFDC64` → `#502800` | Hayır |
| `#F8F8D0` | 3D Extrude 3-color | `#CE47F0` → `#B4641E` → `#59C41C`; gövde `#FFF0B4` | Hayır |
| `#F8F8C4` | Noise | `#FFFFFF` | Hayır |
| `#F8F8C8` | Liquid Morph | `#50C8DC` | Hayır |
| `#F8F8D4` | Water | Su `#2896F0`, kuru bölüm `#3C3C50` | Hayır |
| `#F8F8D8` | Water 80% | Su `#00C8C8`, kuru bölüm `#283C3C` | Hayır |
| `#F8F8DC` | Gri → Beyaz | `#606060` → `#FFFFFF` | Evet |
| `#F8F8E0` | Sarı → Açık sarı | `#CC9C00` → `#FFF480` | Evet |
| `#F8F8E4` | Turuncu → Açık turuncu | `#B84800` → `#FFB45C` | Evet |
| `#F8F8E8` | Mavi → Camgöbeği | `#1860B8` → `#40E0FF` | Evet |
| `#F8F8EC` | Lacivert → Açık lacivert | `#0C2070` → `#4060C0` | Evet |
| `#F8F8F0` | Kırmızı → Açık kırmızı | `#981818` → `#FF6868` | Evet |
| `#F8F8F4` | Yeşil → Açık yeşil | `#147034` → `#60E084` | Evet |
| `#F8F8F8` | Mor → Açık mor | `#501C80` → `#B070E8` | Evet |
| `#F8F8FC` | Pembe → Açık pembe | `#983064` → `#FF90C4` | Evet |
| `#F8FCDC` | Koyu gri → Gri | `#242424` → `#808080` | Evet |
| `#F8FCE0` | Siyah → Füme | `#080808` → `#484848` | Evet |
| `#F8FCE4` | Koyu yeşil → Yeşil | `#084018` → `#34984C` | Evet |
| `#F8FCE8` | Koyu turkuaz → Turkuaz | `#005854` → `#48C8C0` | Evet |
| `#F8FCEC` | Camgöbeği → Açık camgöbeği | `#007088` → `#70ECF8` | Evet |
| `#F8FCF0` | Eflatun → Açık eflatun | `#701868` → `#E870DC` | Evet |
| `#F8FCF4` | Kahverengi → Açık kahverengi | `#5C3418` → `#BC7C4C` | Evet |
| `#F8FCF8` | Akan Gri ↔ Beyaz (←) | `#606060` ↔ `#FFFFFF` | Evet |
| `#F8FCFC` | Akan Sarı ↔ Açık sarı (←) | `#CC9C00` ↔ `#FFF480` | Evet |
| `#FCF8DC` | Akan Turuncu ↔ Açık turuncu (←) | `#B84800` ↔ `#FFB45C` | Evet |
| `#FCF8E0` | Akan Mavi ↔ Camgöbeği (←) | `#1860B8` ↔ `#40E0FF` | Evet |
| `#FCF8E4` | Akan Lacivert ↔ Açık lacivert (←) | `#0C2070` ↔ `#4060C0` | Evet |
| `#FCF8E8` | Akan Kırmızı ↔ Açık kırmızı (←) | `#981818` ↔ `#FF6868` | Evet |
| `#FCF8EC` | Akan Yeşil ↔ Açık yeşil (←) | `#147034` ↔ `#60E084` | Evet |
| `#FCF8F0` | Akan Mor ↔ Açık mor (←) | `#501C80` ↔ `#B070E8` | Evet |
| `#FCF8F4` | Akan Pembe ↔ Açık pembe (←) | `#983064` ↔ `#FF90C4` | Evet |
| `#FCF8F8` | Akan Koyu gri ↔ Gri (←) | `#242424` ↔ `#808080` | Evet |
| `#FCF8FC` | Akan Siyah ↔ Füme (←) | `#080808` ↔ `#484848` | Evet |
| `#FCFCDC` | Akan Koyu yeşil ↔ Yeşil (←) | `#084018` ↔ `#34984C` | Evet |
| `#FCFCE0` | Akan Koyu turkuaz ↔ Turkuaz (←) | `#005854` ↔ `#48C8C0` | Evet |
| `#FCFCE4` | Akan Camgöbeği ↔ Açık camgöbeği (←) | `#007088` ↔ `#70ECF8` | Evet |
| `#FCFCE8` | Akan Eflatun ↔ Açık eflatun (←) | `#701868` ↔ `#E870DC` | Evet |
| `#FCFCEC` | Akan Kahverengi ↔ Açık kahverengi (←) | `#5C3418` ↔ `#BC7C4C` | Evet |

## Kullanılabilir efekt API'si

Paket shake, wavy, rainbow, bouncy, blinking, pulse, spin, sequential spin, fade, iterating, glitch, scale/offset, static/dynamic gradient, lava, color override, aurora, split, outline, hatch, neon, chromatic aberration, 3D extrude, noise, liquid ve water efektlerini içerir. Parametreler ve birleştirme kuralları için [CONFIGURATION.md](./CONFIGURATION.md) dosyasını kullanın.

## Doğrulama ve release ZIP'i

```sh
python scripts/validate_pack.py
python scripts/build_release.py --output dist/Text-Effects-v1.3.2.zip
python scripts/validate_pack.py --zip dist/Text-Effects-v1.3.2.zip
```

Mojang'ın SHA-1 doğrulamalı resmî istemci JAR'larıyla shader ABI sınır kontrolü:

```sh
python scripts/verify_mojang_abi.py --include-snapshot
```

26.2 ve 26.3 shader varyantları ayrıca resmî istemci JAR'ı ve Khronos `glslang`
ile derlenip bağlanabilir. `verify_26_2_compile.py`, normal, GUI, grayscale,
see-through ve 26.3 OIT geçişlerini kapsar; istemci JAR'ının beklenen SHA-1
değerini zorunlu olarak doğrular.

ItemsAdder 5 ile kullanılacak dağıtımda release ZIP'i tercih edilmelidir. Build
aracı bakım yapılabilir kaynakları değiştirmeden ZIP içindeki shader yorumlarını
ve gereksiz boşlukları güvenli biçimde küçültür. Paket yalnız metin core
shader'larını içerir; ItemsAdder'ın eşya, zırh, entity veya terrain shader'larını
ezmez. `iazip` komutunun ZIP üretmesi, native GLSL doğrulamasının geçtiği
anlamına gelmez; sunucu günlüğündeki shader doğrulama sonucu ayrıca kontrol
edilmelidir.

ZIP'in kökünde doğrudan `pack.mcmeta`, `pack.png`, `LICENSE`, `assets/` ve overlay klasörleri bulunur; fazladan üst klasör yoktur.

## Kredi ve lisans

Orijinal proje: [TheSalt's Text Effects](https://github.com/TheSalts/Text_Effects), Copyright © 2026 TheSalt_. Bu fork MIT Lisansı altında dağıtılır ve [LICENSE](./LICENSE) dosyası release paketinde korunur.

Proje ilk olarak [Text-Effects-by-Akis](https://github.com/YeahAkis/Text-Effects-by-Akis) çalışmasından ilham almıştır. Orijinal projedeki özel teşekkür: 좌우반전 코드를 제공해 주신 [@베스트견과류](https://github.com/bestnuts) 님에게 감사를 표합니다.
