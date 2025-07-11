import requests
from collections import defaultdict
import base64
from urllib.parse import quote
import sys
import argparse
import configparser
import os
from pathlib import Path

import configparser
import os
from pathlib import Path

# ANSI Color codes for terminal output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'  # Reset to default color

def load_config():
    """Konfigürasyon dosyasından ve ortam değişkenlerinden ayarları yükle"""
    config = configparser.ConfigParser()
    
    # Konfigürasyon dosyasının yolunu bul
    config_path = Path(__file__).parent / 'config.ini'
    
    if not config_path.exists():
        print(f"❌ Konfigürasyon dosyası bulunamadı: {config_path}")
        print("Lütfen config.ini dosyasını oluşturun veya örnekten kopyalayın.")
        exit(1)
    
    config.read(config_path)
    
    # .env dosyasından ortam değişkenlerini yükle
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    
    return config

def get_setting(config, section, key, default=None, env_var=None):
    """Konfigürasyondan ayar al, önce ortam değişkenini kontrol et"""
    # Önce ortam değişkenini kontrol et
    if env_var and env_var in os.environ:
        return os.environ[env_var]
    
    # Sonra config dosyasından al
    try:
        return config.get(section, key)
    except (configparser.NoSectionError, configparser.NoOptionError):
        return default

# Ayarlar - Global değişkenler yerine fonksiyon içinde tanımlanacak
def load_azure_settings():
    """Azure ayarlarını yükle"""
    config = load_config()
    
    settings = {
        'organization': get_setting(config, 'Azure', 'organization', 'KocDigitalOrganization', 'AZURE_ORGANIZATION'),
        'project': get_setting(config, 'Azure', 'project', 'KocDigital - Agile Teams', 'AZURE_PROJECT'), 
        'team': get_setting(config, 'Azure', 'team', 'Atmaca', 'AZURE_TEAM'),
        'pat': get_setting(config, 'Azure', 'pat', None, 'AZURE_PAT'),
        'default_sprint': get_setting(config, 'Analysis', 'default_sprint', '51'),
        'working_days': int(get_setting(config, 'Analysis', 'working_days', '9')),
        'debug': get_setting(config, 'Analysis', 'debug', 'false').lower() == 'true',
        'max_projects_display': int(get_setting(config, 'Output', 'max_projects_display', '10')),
        'sprint_column_width': int(get_setting(config, 'Output', 'sprint_column_width', '15')),
        'activity_column_width': int(get_setting(config, 'Output', 'activity_column_width', '20')),
        'numeric_column_width': int(get_setting(config, 'Output', 'numeric_column_width', '20')),
        'resource_need_column_width': int(get_setting(config, 'Output', 'resource_need_column_width', '20'))
    }
    
    if not settings['pat'] or settings['pat'] == 'YOUR_PAT_HERE':
        print("❌ Azure DevOps Personal Access Token (PAT) bulunamadı!")
        print("Lütfen aşağıdakilerden birini yapın:")
        print("1. config.ini dosyasında 'pat' değerini ayarlayın")
        print("2. .env dosyasında AZURE_PAT değişkenini ayarlayın")
        print("3. Ortam değişkeni olarak AZURE_PAT'ı ayarlayın")
        print("\nPAT oluşturmak için: https://dev.azure.com/[your-org]/_usersSettings/tokens")
        exit(1)
    
    return settings

# Global değişkenleri kaldırıp settings kullanacağız
settings = load_azure_settings()

# URL encode the components
organization_encoded = quote(settings['organization'])
project_encoded = quote(settings['project'])
team_encoded = quote(settings['team'])

if settings['debug']:
    print(f"Debug: Original organization: {settings['organization']}")
    print(f"Debug: Encoded organization: {organization_encoded}")
    print(f"Debug: Original project: {settings['project']}")
    print(f"Debug: Encoded project: {project_encoded}")
    print(f"Debug: PAT length: {len(settings['pat'])}")
    print(f"Debug: PAT first 4 chars: {settings['pat'][:4]}...")
    print(f"Debug: PAT last 4 chars: ...{settings['pat'][-4:]}")

# API URL'leri
base_url = f"https://dev.azure.com/{organization_encoded}"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Basic {base64.b64encode((':'+settings['pat']).encode()).decode()}"
}

# Test different possible organization names and basic connectivity
def test_organization_variations():
    variations = [
        "KoçDigitalOrganization",
        "KocDigitalOrganization", 
        "KocDigital",
        "kocdigital",
        "Koc-Digital",
        "koc-digital"
    ]
    
    for org_name in variations:
        print(f"\n🔍 Testing organization: '{org_name}'")
        encoded_org = quote(org_name)
        test_url = f"https://dev.azure.com/{encoded_org}/_apis/projects?api-version=7.0"
        
        try:
            res = requests.get(test_url, headers=headers, timeout=10)
            print(f"   Status: {res.status_code}")
            
            if res.status_code == 200:
                projects = res.json()
                print(f"   ✅ Success! Found {len(projects.get('value', []))} projects")
                for proj in projects.get('value', [])[:3]:  # Show first 3 projects
                    print(f"      - {proj.get('name', 'Unknown')}")
                return org_name
            elif res.status_code == 401:
                print("   ❌ Authentication failed - Check your PAT permissions")
            elif res.status_code == 403:
                print("   ❌ Access forbidden - PAT might not have access to this org")
            elif res.status_code == 404:
                print("   ❌ Organization not found")
            else:
                print(f"   ❌ Unexpected error: {res.status_code}")
                
        except requests.exceptions.Timeout:
            print("   ❌ Request timed out")
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request failed: {e}")
    
    return None
# Test basic connectivity first
def test_connectivity():
    # Try to get basic organization info
    url = f"{base_url}/_apis/projects?api-version=7.0"
    if settings['debug']:
        print(f"Debug: Testing basic connectivity with URL: {url}")
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if settings['debug']:
            print(f"Debug: Response status: {res.status_code}")
        if res.status_code == 200:
            projects = res.json()
            if settings['debug']:
                print(f"Debug: Found {len(projects.get('value', []))} projects")
                for proj in projects.get('value', [])[:settings['max_projects_display']]:
                    print(f"  - Project: {proj.get('name', 'Unknown')}")
            return True
        else:
            if settings['debug']:
                print(f"Debug: Response text: {res.text}")
            return False
    except Exception as e:
        if settings['debug']:
            print(f"Debug: Error during connectivity test: {e}")
        return False

def get_iteration_id(iteration_name):
    url = f"{base_url}/{project_encoded}/{team_encoded}/_apis/work/teamsettings/iterations?api-version=7.0"
    if settings['debug']:
        print(f"Debug: Requesting URL: {url}")
    res = requests.get(url, headers=headers)
    if settings['debug']:
        print(f"Debug: Response status: {res.status_code}")
    if res.status_code != 200:
        if settings['debug']:
            print(f"Debug: Response text: {res.text}")
    res.raise_for_status()
    
    iterations = res.json()["value"]
    if settings['debug']:
        print(f"Debug: Found {len(iterations)} iterations:")
        for it in iterations:
            print(f"  - Name: {it['name']}, Path: {it.get('path', 'No path')}")
    for it in iterations:
        if it["name"] == iteration_name:
            return it["id"], it.get("path", "")
    raise Exception(f"Sprint '{iteration_name}' bulunamadı.")

# 2. Capacity'yi aktiviteye göre grupla
def get_capacity_by_activity(iteration_id):
    url = f"{base_url}/{project_encoded}/{team_encoded}/_apis/work/teamsettings/iterations/{iteration_id}/capacities?api-version=7.0"
    if settings['debug']:
        print(f"Debug: Getting capacity from URL: {url}")
    res = requests.get(url, headers=headers)
    if settings['debug']:
        print(f"Debug: Capacity response status: {res.status_code}")
    res.raise_for_status()

    capacity_by_activity = defaultdict(float)
    response_data = res.json()
    if settings['debug']:
        print(f"Debug: Capacity response data: {response_data}")
    
    # Handle both direct list and value wrapper
    members = response_data if isinstance(response_data, list) else response_data.get("value", [])
    
    # If there's a teamMembers wrapper, use that
    if "teamMembers" in response_data:
        members = response_data["teamMembers"]
    
    for member in members:
        if settings['debug']:
            print(f"Debug: Processing member: {member}")
        if isinstance(member, dict):
            for act in member.get("activities", []):
                if isinstance(act, dict):
                    activity_name = act.get("name", "Unknown")
                    capacity_per_day = act.get("capacityPerDay", 0)
                    capacity_by_activity[activity_name] += capacity_per_day
                    if settings['debug']:
                        print(f"Debug: Added {capacity_per_day} capacity for activity: {activity_name}")
    return capacity_by_activity

# 3. Work item'ları al (WIQL ile)
def get_work_items_ids(iteration_path):
    wiql = {
        "query": f"""
        SELECT [System.Id]
        FROM WorkItems
        WHERE [System.IterationPath] = '{iteration_path}'
          AND [System.WorkItemType] = 'Task'
        """
    }
    url = f"{base_url}/{project_encoded}/_apis/wit/wiql?api-version=7.0"
    if settings['debug']:
        print(f"Debug: WIQL URL: {url}")
        print(f"Debug: WIQL Query: {wiql['query']}")
    res = requests.post(url, headers=headers, json=wiql)
    if settings['debug']:
        print(f"Debug: WIQL Response status: {res.status_code}")
    if res.status_code != 200:
        if settings['debug']:
            print(f"Debug: WIQL Response text: {res.text}")
    res.raise_for_status()
    return [item["id"] for item in res.json()["workItems"]]

# 4. Work item detayları ve aktiviteye göre grup
def get_work_hours_by_activity(work_item_ids):
    chunks = [work_item_ids[i:i+200] for i in range(0, len(work_item_ids), 200)]
    work_by_activity = defaultdict(float)

    for chunk in chunks:
        ids_str = ",".join(map(str, chunk))
        url = f"{base_url}/{project_encoded}/_apis/wit/workitems?ids={ids_str}&fields=Microsoft.VSTS.Common.Activity,Microsoft.VSTS.Scheduling.OriginalEstimate&api-version=7.0"
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        for item in res.json()["value"]:
            fields = item.get("fields", {})
            activity = fields.get("Microsoft.VSTS.Common.Activity")
            hours = fields.get("Microsoft.VSTS.Scheduling.OriginalEstimate", 0)
            if activity:
                work_by_activity[activity] += hours
    return work_by_activity

# Tek bir sprint için analiz yapan fonksiyon
def analyze_sprint(sprint_name):
    print(f"\n� {sprint_name} analiz ediliyor...")
    
    try:
        iteration_id, iteration_path = get_iteration_id(sprint_name)
        print(f"✅ {sprint_name} bulundu! Path: {iteration_path}")
        
        print(f"🔄 {sprint_name} kapasite verisi alınıyor...")
        capacity_data = get_capacity_by_activity(iteration_id)
        
        print(f"� {sprint_name} work item listesi alınıyor...")
        work_ids = get_work_items_ids(iteration_path)
        
        print(f"📊 {sprint_name} planlanan iş yükü hesaplanıyor...")
        work_data = get_work_hours_by_activity(work_ids)
        
        return sprint_name, capacity_data, work_data
        
    except Exception as e:
        print(f"❌ {sprint_name} analiz edilemedi: {e}")
        return sprint_name, {}, {}

def parse_sprint_range(sprint_range):
    """Sprint aralığını parse et. Örnek: '50-55' -> [50, 51, 52, 53, 54, 55]"""
    if '-' in sprint_range:
        start, end = sprint_range.split('-')
        return list(range(int(start), int(end) + 1))
    else:
        return [int(sprint_range)]

# Kişi bazında kapasite analizi
def get_team_members_capacity(iteration_id):
    """Her takım üyesi için kapasite bilgilerini al"""
    url = f"{base_url}/{project_encoded}/{team_encoded}/_apis/work/teamsettings/iterations/{iteration_id}/capacities?api-version=7.0"
    if settings['debug']:
        print(f"Debug: Getting team members capacity from URL: {url}")
    res = requests.get(url, headers=headers)
    if settings['debug']:
        print(f"Debug: Team capacity response status: {res.status_code}")
    res.raise_for_status()

    response_data = res.json()
    members_capacity = {}
    
    # Handle both direct list and value wrapper
    members = response_data if isinstance(response_data, list) else response_data.get("value", [])
    
    # If there's a teamMembers wrapper, use that
    if "teamMembers" in response_data:
        members = response_data["teamMembers"]
    
    for member in members:
        if isinstance(member, dict):
            display_name = member["teamMember"]["displayName"]
            activities = member.get("activities", [])
            
            if display_name not in members_capacity:
                members_capacity[display_name] = {}
            
            for activity in activities:
                if isinstance(activity, dict):
                    activity_name = activity.get("name", "Unknown")
                    capacity_per_day = activity.get("capacityPerDay", 0)
                    total_capacity = capacity_per_day * settings['working_days']
                    members_capacity[display_name][activity_name] = total_capacity
                    
                    if settings['debug']:
                        print(f"Debug: {display_name} - {activity_name}: {capacity_per_day}/day * {settings['working_days']} = {total_capacity}h total")
    
    return members_capacity

def get_work_hours_by_member_and_activity(work_item_ids):
    """Work item'ları member ve aktiviteye göre grupla"""
    chunks = [work_item_ids[i:i+200] for i in range(0, len(work_item_ids), 200)]
    work_by_member_activity = defaultdict(lambda: defaultdict(float))

    for chunk in chunks:
        ids_str = ",".join(map(str, chunk))
        url = f"{base_url}/{project_encoded}/_apis/wit/workitems?ids={ids_str}&fields=System.AssignedTo,Microsoft.VSTS.Common.Activity,Microsoft.VSTS.Scheduling.OriginalEstimate&api-version=7.0"
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        
        for item in res.json()["value"]:
            fields = item.get("fields", {})
            
            # Assigned To field'ından kişi adını al
            assigned_to = fields.get("System.AssignedTo")
            if assigned_to and isinstance(assigned_to, dict):
                member_name = assigned_to.get("displayName", "Unassigned")
            else:
                member_name = "Unassigned"
            
            activity = fields.get("Microsoft.VSTS.Common.Activity", "Unknown")
            hours = fields.get("Microsoft.VSTS.Scheduling.OriginalEstimate", 0)
            
            if hours and hours > 0:
                work_by_member_activity[member_name][activity] += hours
                
                if settings['debug']:
                    print(f"Debug: {member_name} - {activity}: +{hours}h")
    
    return work_by_member_activity

def generate_capacity_report(sprint_numbers, all_results):
    """Kişi bazında kapasite raporu oluştur"""
    print(f"\n👥 Kişi Bazında Kapasite Analizi:")
    print("=" * 90)
    
    for sprint_num in sprint_numbers:
        sprint_name = f"Sprint {sprint_num}"
        print(f"\n📋 {sprint_name}:")
        print("-" * 90)
        
        try:
            # Sprint bilgilerini al
            iteration_id, iteration_path = get_iteration_id(sprint_name)
            
            # Kişi bazında kapasiteleri al
            members_capacity = get_team_members_capacity(iteration_id)
            
            # Work item'ları al
            work_ids = get_work_items_ids(iteration_path)
            
            # Kişi ve aktivite bazında planlanan işleri al
            work_by_member = get_work_hours_by_member_and_activity(work_ids)
            
            # Tüm kişileri topla (hem kapasite hem work'te olanları)
            all_members = set(members_capacity.keys()) | set(work_by_member.keys())
            
            print(f"{'Kişi':<25}{'Aktivite':<20}{'Kapasite (h)':>15}{'Planlanan (h)':>15}{'Yüklenme (%)':>15}")
            print("-" * 90)
            
            for member in sorted(all_members):
                member_total_capacity = 0
                member_total_planned = 0
                
                # Bu kişinin tüm aktivitelerini topla
                activities = set()
                if member in members_capacity:
                    activities.update(members_capacity[member].keys())
                if member in work_by_member:
                    activities.update(work_by_member[member].keys())
                
                # Aktivite bazında göster
                for activity in sorted(activities):
                    capacity = members_capacity.get(member, {}).get(activity, 0)
                    planned = work_by_member.get(member, {}).get(activity, 0)
                    
                    if capacity > 0 or planned > 0:
                        utilization = (planned / capacity * 100) if capacity > 0 else 0
                        
                        # Renk kodu
                        if utilization > 100:
                            utilization_str = f"{Colors.RED}{utilization:.1f}%{Colors.RESET}"
                        elif utilization > 90:
                            utilization_str = f"{Colors.YELLOW}{utilization:.1f}%{Colors.RESET}"
                        else:
                            utilization_str = f"{utilization:.1f}%"
                        
                        print(f"{member:<25}{activity:<20}{capacity:>15.1f}{planned:>15.1f}{utilization_str:>25}")
                        
                        member_total_capacity += capacity
                        member_total_planned += planned
                
                # Kişi toplamı
                if member_total_capacity > 0 or member_total_planned > 0:
                    total_utilization = (member_total_planned / member_total_capacity * 100) if member_total_capacity > 0 else 0
                    
                    if total_utilization > 100:
                        total_util_str = f"{Colors.RED}{Colors.BOLD}{total_utilization:.1f}%{Colors.RESET}"
                    elif total_utilization > 90:
                        total_util_str = f"{Colors.YELLOW}{Colors.BOLD}{total_utilization:.1f}%{Colors.RESET}"
                    else:
                        total_util_str = f"{Colors.BOLD}{total_utilization:.1f}%{Colors.RESET}"
                    
                    print(f"{'':<25}{Colors.BOLD}{'TOPLAM':<20}{member_total_capacity:>15.1f}{member_total_planned:>15.1f}{total_util_str:>25}")
                    print("-" * 90)
        
        except Exception as e:
            print(f"❌ {sprint_name} kişi bazında analiz edilemedi: {e}")

# Ana akış
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Azure DevOps Sprint Analysis')
    parser.add_argument('sprints', nargs='?', default='51', 
                       help='Sprint number or range (e.g., "51" or "50-55")')
    parser.add_argument('--report', choices=['default', 'capacity', 'trend', 'workitem-types', 'all'], 
                       default='default',
                       help='Report type to generate')
    
    args = parser.parse_args()
    
    print("🔄 Testing basic connectivity...")
    if not test_connectivity():
        print("❌ Basic connectivity failed. Please check your PAT and organization name.")
        exit(1)
    
    print("✅ Basic connectivity successful!")
    
    # Sprint aralığını parse et
    sprint_numbers = parse_sprint_range(args.sprints)
    print(f"📋 Analiz edilecek sprintler: {sprint_numbers}")
    print(f"📊 Rapor türü: {args.report}")
    
    # Sadece capacity raporu isteniyorsa
    if args.report == 'capacity':
        generate_capacity_report(sprint_numbers, [])
        exit(0)
    
    # Varsayılan rapor (mevcut analiz)
    if args.report in ['default', 'all']:
        # Tüm sonuçları topla
        all_results = []
        
        for sprint_num in sprint_numbers:
            sprint_name = f"Sprint {sprint_num}"
            sprint_name, capacity_data, work_data = analyze_sprint(sprint_name)
            
            # Her aktivite için sonuçları kaydet
            activities = sorted(set(capacity_data.keys()).union(work_data.keys()))
            for activity in activities:
                planned = round(work_data.get(activity, 0), 1)
                capacity = round(capacity_data.get(activity, 0) * settings['working_days'], 1)
                resource_need = max(0, planned - capacity)  # Sadece pozitif değerler
                all_results.append({
                    'Sprint': sprint_name,
                    'Activity': activity,
                    'Planned Work (h)': planned,
                    'Capacity (h)': capacity,
                    'Resource Need (h)': resource_need
                })
        
        # Sonuçları yazdır
        print(f"\n📋 Sprint Analiz Özeti:\n")
        print(f"{'Sprint':<15}{'Activity':<20}{'Planned Work (h)':>20}{'Capacity (h)':>20}{'Resource Need (h)':>20}")
        print("-" * 95)
        
        for result in all_results:
            resource_need = result['Resource Need (h)']
            if resource_need > 0:
                # Kırmızı renkte göster eğer kaynak ihtiyacı varsa
                resource_need_str = f"{Colors.RED}{resource_need:.1f}{Colors.RESET}"
            else:
                resource_need_str = f"{resource_need:.1f}"
                
            print(f"{result['Sprint']:<15}{result['Activity']:<20}{result['Planned Work (h)']:>20}{result['Capacity (h)']:>20}{resource_need_str:>30}")
            
        # Özet istatistikler
        if all_results:
            print(f"\n📊 Genel Özet:")
            total_planned = sum(r['Planned Work (h)'] for r in all_results)
            total_capacity = sum(r['Capacity (h)'] for r in all_results)
            total_resource_need = sum(r['Resource Need (h)'] for r in all_results)
            print(f"Toplam Planlanan İş: {total_planned:.1f} saat")
            print(f"Toplam Kapasite: {total_capacity:.1f} saat")
            print(f"Kapasite Kullanım Oranı: {(total_planned/total_capacity*100) if total_capacity > 0 else 0:.1f}%")
            if total_resource_need > 0:
                print(f"{Colors.RED}Toplam Kaynak İhtiyacı: {total_resource_need:.1f} saat{Colors.RESET}")
            else:
                print(f"{Colors.GREEN}✅ Kaynak ihtiyacı yok - kapasite yeterli{Colors.RESET}")
            
            # Sprint bazında kaynak ihtiyaçları özeti
            print(f"\n🚨 Sprint Bazında Kaynak İhtiyaçları:")
            
            # Sprint bazında grupla
            sprint_needs = {}
            for result in all_results:
                if result['Resource Need (h)'] > 0:  # Sadece ihtiyaç olanları göster
                    sprint = result['Sprint']
                    if sprint not in sprint_needs:
                        sprint_needs[sprint] = []
                    sprint_needs[sprint].append({
                        'Activity': result['Activity'],
                        'Need': result['Resource Need (h)']
                    })
            
            if sprint_needs:
                print(f"{'Sprint':<15}{'Activity':<20}{'İhtiyaç (saat)':>15}")
                print("-" * 50)
                
                for sprint in sorted(sprint_needs.keys()):
                    # Sprint başına toplam ihtiyaç
                    sprint_total = sum(item['Need'] for item in sprint_needs[sprint])
                    print(f"\n{Colors.BOLD}{sprint:<15}{'TOPLAM':<20}{Colors.RED}{sprint_total:.1f}{Colors.RESET}")
                    
                    # Aktivite bazında detaylar
                    for item in sorted(sprint_needs[sprint], key=lambda x: x['Need'], reverse=True):
                        print(f"{'':>15}{item['Activity']:<20}{Colors.RED}{item['Need']:.1f}{Colors.RESET}")
            else:
                print(f"{Colors.GREEN}✅ Hiçbir sprintte kaynak ihtiyacı yok!{Colors.RESET}")
            
            # Aktivite bazında kaynak ihtiyaçları özeti
            print(f"\n📊 Aktivite Bazında Kaynak İhtiyaçları:")
            
            # Aktivite bazında grupla
            activity_needs = {}
            for result in all_results:
                if result['Resource Need (h)'] > 0:  # Sadece ihtiyaç olanları göster
                    activity = result['Activity']
                    if activity not in activity_needs:
                        activity_needs[activity] = []
                    activity_needs[activity].append({
                        'Sprint': result['Sprint'],
                        'Need': result['Resource Need (h)']
                    })
            
            if activity_needs:
                print(f"{'Activity':<20}{'Sprint':<15}{'İhtiyaç (saat)':>15}")
                print("-" * 50)
                
                # Toplam ihtiyaca göre aktiviteleri sırala
                activity_totals = {}
                for activity, items in activity_needs.items():
                    activity_totals[activity] = sum(item['Need'] for item in items)
                
                for activity in sorted(activity_totals.keys(), key=lambda x: activity_totals[x], reverse=True):
                    # Aktivite başına toplam ihtiyaç
                    activity_total = activity_totals[activity]
                    print(f"\n{Colors.BOLD}{activity:<20}{'TOPLAM':<15}{Colors.RED}{activity_total:.1f}{Colors.RESET}")
                    
                    # Sprint bazında detaylar (ihtiyaca göre sıralı)
                    for item in sorted(activity_needs[activity], key=lambda x: x['Need'], reverse=True):
                        print(f"{'':>20}{item['Sprint']:<15}{Colors.RED}{item['Need']:.1f}{Colors.RESET}")
            else:
                print(f"{Colors.GREEN}✅ Hiçbir aktivitede kaynak ihtiyacı yok!{Colors.RESET}")
    
    # Capacity raporu da isteniyorsa
    if args.report == 'all':
        generate_capacity_report(sprint_numbers, all_results)
