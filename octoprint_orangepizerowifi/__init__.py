# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
import logging
from flask import jsonify, make_response
from octoprint.server import admin_permission

CONFIG_COMMAND = "wpa_config"

class OrangepizerowifiPlugin(octoprint.plugin.SettingsPlugin,
                             octoprint.plugin.AssetPlugin,
                             octoprint.plugin.TemplatePlugin,
                             octoprint.plugin.SimpleApiPlugin,
                             octoprint.plugin.ShutdownPlugin,
                             octoprint.plugin.StartupPlugin):

	##~~ SettingsPlugin mixin

	def get_settings_defaults(self):
		return dict(
			# put your plugin's default settings here
		)


        ##~~ TemplatePlugin API
	def get_template_configs(self):
		return [
			dict(type="settings", name="Wi-Fi")
		]
        
        ##~~ SimpleApiPlugin API
	def get_api_commands(self):
		return dict(
			add_ap=["ap_name", "ap_psk"],
			del_ap=["ap_name"],
                        list_ap=[],
		)
                
        def is_api_adminonly(self):
		return True
            
        def on_api_get(self, request):
            try:
                wifis = self._list_ap()
            except Exception as e:
                return jsonify(dict(error=e.message))
            
            return jsonify(dict(
                    wifis=wifis
            ))
            
        def on_api_command(self, command, data):
            if command == "list_ap":
                return jsonify(self._list_ap())
            if not admin_permission.can():
		return make_response("Insufficient rights", 403)    
            if command == "add_ap":
                self._add_ap(data["ap_name"], data["ap_psk"], force=data["force"] if "force" in data else False)
            if command == "del_ap":
                self._del_ap(data["ap_name"])

	##~~ AssetPlugin mixin

	def get_assets(self):
		# Define your plugin's asset files to automatically include in the
		# core UI here.
		return dict(
			js=["js/orangepizerowifi.js"],
			css=["css/orangepizerowifi.css"],
			less=["less/orangepizerowifi.less"]
		)
                
        ##~~ ShutdownPlugin API
        def on_shutdown(self):
            self._make()
            
        ##~~ StartupPlugin API
        def on_after_startup(self):
            self._migrate()        
        
        ##~~ Private helpers
        
        def _list_ap(self):
            flag, content = self._send_message("list")
            if not flag:
	        raise RuntimeError("Error while listing wifi: " + content)
            result = []
            for wifi in content:
                result.append(wifi)
            return result
        
        def _add_ap(self, ssid, psk, force=False):
            if not psk:
                psk = "-o"
            message = "add" + " " + ssid + " " + psk
            if force:
                message += "-f"
            flag, content = self._send_message(message)
            if not flag:
		raise RuntimeError("Error while add wifi: " + content)
        
        def _del_ap(self, ssid):
            message = "del" + " " + ssid
            flag, content = self._send_message(message)
            if not flag:
		raise RuntimeError("Error while delete wifi: " + content)
            
        def _migrate(self):
            flag, content = self._send_message("migrate")
            if not flag:
	        raise RuntimeError("Error while migrating wifi: " + content)
        
        def _make(self):
            flag, content = self._send_message("make")
            if not flag:
	        raise RuntimeError("Error while making wifi: " + content)
        
        def _send_message(self, message):
            import subprocess
            command = CONFIG_COMMAND + " " + message
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            output, error = process.communicate()
            
            if not error:
                result = ''.join(output)
                return True, result.split('\n')[:-1]
            else:    
               return False, error
        
	##~~ Softwareupdate hook

	def get_update_information(self):
		# Define the configuration for your plugin to use with the Software Update
		# Plugin here. See https://github.com/foosel/OctoPrint/wiki/Plugin:-Software-Update
		# for details.
		return dict(
			orangepizerowifi=dict(
				displayName="Orangepizerowifi Plugin",
				displayVersion=self._plugin_version,

				# version check: github repository
				type="github_release",
				user="frylock34",
				repo="Orange Pi Zero Wi-Fi",
				current=self._plugin_version,

				# update method: pip
				pip="https://github.com/frylock34/orangepizerowifi/archive/{target_version}.zip"
			)
		)


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Orangepizerowifi Plugin"

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = OrangepizerowifiPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
	}

