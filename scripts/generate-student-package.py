#!/usr/bin/env python3
"""
Generate a student connection package (SmartProxy config + CA cert + SSH key).

Usage:
    python3 generate-student-package.py <vm_name> <vm_ip> <pkg_dir> <ca_der_path> <ssh_private_key_path>
"""
import json, shutil, sys, os, stat

name            = sys.argv[1]
ip              = sys.argv[2]
pkg_dir         = sys.argv[3]
ca_der_src      = sys.argv[4]
ssh_key_src     = sys.argv[5]

proxy_config = {
    "product": "SmartProxy",
    "version": "1.3.0",
    "proxyProfiles": [
        {
            "enabled": True, "proxyRules": [], "rulesSubscriptions": [],
            "profileType": 0, "profileId": "InternalProfile_Direct",
            "profileName": "Direct (No Proxy)", "profileProxyServerId": None,
            "profileTypeConfig": {
                "builtin": True, "editable": False, "selectable": True,
                "supportsSubscriptions": False, "supportsProfileProxy": False,
                "customProxyPerRule": False, "canBeDisabled": False,
                "supportsRuleActionWhitelist": False, "defaultRuleActionIsWhitelist": None
            }
        },
        {
            "enabled": True,
            "proxyRules": [{
                "enabled": True, "whiteList": False,
                "ruleId": 546100000000001, "autoGeneratePattern": True,
                "ruleType": 5, "hostName": "sans.labs",
                "rulePattern": "", "ruleRegex": "", "ruleExact": "",
                "proxy": None, "proxyServerId": "-2",
                "ruleSearch": "sans.labs"
            }],
            "rulesSubscriptions": [],
            "profileType": 2, "profileId": "InternalProfile_SmartRules",
            "profileName": "SEC546-Lab", "profileProxyServerId": "sec546labproxy",
            "profileTypeConfig": {
                "builtin": True, "editable": True, "selectable": True,
                "supportsSubscriptions": True, "supportsProfileProxy": True,
                "customProxyPerRule": True, "canBeDisabled": True,
                "supportsRuleActionWhitelist": True, "defaultRuleActionIsWhitelist": False
            }
        },
        {
            "enabled": False, "proxyRules": [], "rulesSubscriptions": [],
            "profileType": 3, "profileId": "InternalProfile_AlwaysEnabled",
            "profileName": "Always Enable", "profileProxyServerId": "sec546labproxy",
            "profileTypeConfig": {
                "builtin": True, "editable": True, "selectable": True,
                "supportsSubscriptions": True, "supportsProfileProxy": True,
                "customProxyPerRule": True, "canBeDisabled": True,
                "supportsRuleActionWhitelist": True, "defaultRuleActionIsWhitelist": True
            }
        },
        {
            "enabled": True, "proxyRules": [], "rulesSubscriptions": [],
            "profileType": 1, "profileId": "InternalProfile_SystemProxy",
            "profileName": "System Proxy", "profileProxyServerId": None,
            "profileTypeConfig": {
                "builtin": True, "editable": False, "selectable": True,
                "supportsSubscriptions": False, "supportsProfileProxy": False,
                "customProxyPerRule": False, "canBeDisabled": False,
                "supportsRuleActionWhitelist": False, "defaultRuleActionIsWhitelist": None
            }
        },
        {
            "enabled": True, "proxyRules": [], "rulesSubscriptions": [],
            "profileType": 4, "profileId": "profile-sec546ignfailure",
            "profileName": "Ignore Failure Rules",
            "profileTypeConfig": {
                "builtin": True, "editable": False, "selectable": False,
                "supportsSubscriptions": False, "supportsProfileProxy": False,
                "customProxyPerRule": False, "canBeDisabled": False,
                "supportsRuleActionWhitelist": False, "defaultRuleActionIsWhitelist": None
            }
        }
    ],
    "activeProfileId": "InternalProfile_SmartRules",
    "proxyServers": [{
        "name": "SEC546-Lab",
        "id": "sec546labproxy",
        "order": 1,
        "host": ip,
        "port": "1080",
        "protocol": "SOCKS5",
        "username": "student",
        "password": "StartTheLabs1#",
        "proxyDNS": True,
        "failoverTimeout": None
    }],
    "proxyServerSubscriptions": [],
    "firstEverInstallNotified": True,
    "updateInfo": None,
    "options": {
        "syncSettings": False, "syncActiveProfile": False,
        "syncActiveProxy": False, "detectRequestFailures": True,
        "displayFailedOnBadge": True, "displayAppliedProxyOnBadge": True,
        "displayMatchedRuleOnBadge": True, "refreshTabOnConfigChanges": False,
        "proxyPerOrigin": False, "enableShortcuts": False,
        "shortcutNotification": False, "themeType": 0,
        "themesDark": "themes-cosmo-dark", "activeIncognitoProfileId": "",
        "themesLight": "", "themesLightCustomUrl": "", "themesDarkCustomUrl": ""
    },
    "defaultProxyServerId": "sec546labproxy"
}

with open(f"{pkg_dir}/smartproxy-sec546.json", "w") as f:
    json.dump(proxy_config, f, indent=4)

shutil.copy(ca_der_src, f"{pkg_dir}/sec546-cloud-ca.der")

# Copy per-student SSH private key
ssh_key_dst = f"{pkg_dir}/sec546-student.key"
shutil.copy(ssh_key_src, ssh_key_dst)
os.chmod(ssh_key_dst, stat.S_IRUSR | stat.S_IWUSR)  # chmod 600

print(f"Package generated for {name} ({ip})")
