# Azure DevOps Sprint Analysis Tool

Bu araç Azure DevOps'ta sprint kapasitesi ve planlanan iş yükünü analiz eder, kaynak ihtiyaçlarını belirler.

## 🚀 Kurulum

### 1. Repository'yi klonlayın
```bash
git clone <repository-url>
cd azure-sprint-analysis
```

### 2. Python sanal ortamı oluşturun
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# veya
.venv\Scripts\activate     # Windows
```

### 3. Gerekli paketleri yükleyin
```bash
pip install requests
```

### 4. Konfigürasyon dosyasını oluşturun
```bash
cp config.ini.example config.ini
```

### 5. config.ini dosyasını düzenleyin
```ini
[Azure]
organization = AZURE_DEVOPS_ORG_NAME
project = PROJECT_NAME  
team = TEAM_NAME
pat = YOUR_PERSONAL_ACCESS_TOKEN

[Analysis]
default_sprint = 51
working_days = 9
debug = false
```

## 🔑 Personal Access Token (PAT) Oluşturma

1. Azure DevOps'a gidin: `https://dev.azure.com/[your-org]/_usersSettings/tokens`
2. "New Token" butonuna tıklayın
3. Aşağıdaki izinleri verin:
   - **Work Items**: Read & Write
   - **Project and Team**: Read
4. Token'ı kopyalayın ve config.ini'ye yapıştırın

## 📊 Kullanım

### Tek Sprint Analizi
```bash
python azure.py 51
```

### Sprint Aralığı Analizi  
```bash
python azure.py 50-55
```

### Varsayılan Sprint Analizi
```bash
python azure.py  # config.ini'deki default_sprint kullanılır
```

## 📋 Çıktı Formatı

Araç şu bilgileri gösterir:

1. **Sprint Analiz Tablosu**:
   - Sprint adı
   - Aktivite türü (Development, Testing, UI Development, etc.)
   - Planlanan iş (saat)
   - Mevcut kapasite (saat)
   - Kaynak ihtiyacı (saat) - kırmızı renkte

2. **Genel Özet**:
   - Toplam planlanan iş
   - Toplam kapasite
   - Kapasite kullanım oranı

3. **Sprint Bazında Kaynak İhtiyaçları**:
   - Her sprint için toplam kaynak eksikliği
   - Aktivite bazında detaylı liste

## ⚙️ Konfigürasyon

### config.ini Seçenekleri

```ini
[Azure]
organization = Azure DevOps organizasyon adı
project = Proje adı
team = Takım adı  
pat = Personal Access Token (boş bırakabilirsiniz)

[Analysis]
default_sprint = Varsayılan sprint numarası
working_days = Sprint başına çalışma günü sayısı
debug = Debug çıktısını göster (true/false)

[Output]
max_projects_display = Bağlantı testinde gösterilecek max proje sayısı
sprint_column_width = Sprint kolonu genişliği
activity_column_width = Aktivite kolonu genişliği
numeric_column_width = Sayısal kolonlar genişliği
resource_need_column_width = Kaynak ihtiyacı kolonu genişliği
```

### Alternatif PAT Yöntemi (.env dosyası)

Güvenlik için PAT'ı ayrı bir `.env` dosyasında da saklayabilirsiniz:

```bash
# .env dosyası oluşturun
echo "AZURE_PAT=your_token_here" > .env
```

## 🛠️ Sorun Giderme

### 401 Authentication Error
- PAT'ınızın doğru olduğundan emin olun
- PAT'ın gerekli izinlere sahip olduğunu kontrol edin
- PAT'ın süresi dolmamış olduğundan emin olun

### 404 Not Found Error
- Organizasyon, proje ve takım adlarının doğru olduğunu kontrol edin
- Türkçe karakterler varsa İngilizce karşılıklarını deneyin

### Sprint Bulunamadı Hatası
- Sprint adının tam olarak Azure DevOps'taki ile aynı olduğunu kontrol edin
- Debug modunu açarak (`debug = true`) mevcut sprintleri görün

## 🎯 Örnek Çıktı

```
📋 Sprint Analiz Özeti:

Sprint         Activity            Planned Work (h)    Capacity (h)   Resource Need (h)
-----------------------------------------------------------------------------------------
Sprint 51      Development                    514.0           351.0               163.0
Sprint 51      Testing                         95.0           216.0                 0.0
Sprint 51      UI Development                  88.0            72.0                16.0

🚨 Sprint Bazında Kaynak İhtiyaçları:
Sprint         Activity             İhtiyaç (saat)
--------------------------------------------------

Sprint 51      TOPLAM              179.0
               Development         163.0
               UI Development      16.0
```

## 📝 Notlar

- Bu araç sadece 'Task' tipindeki work item'ları analiz eder
- Kapasite hesaplaması config.ini'deki `working_days` değeri ile yapılır
- Kaynak ihtiyacı sadece pozitif değerler (eksiklik) için gösterilir
- Renkli çıktı için terminal ANSI color desteği gereklidir

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun
3. Değişikliklerinizi commit edin  
4. Pull request gönderin

## 📄 Lisans

Bu proje MIT lisansı altında sunulmaktadır.
