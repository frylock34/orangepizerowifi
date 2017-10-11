/*
 * View model for Orange Pi Zero Wi-Fi
 *
 * Author: Ilia gushchin[D[D[D[D[D[D[G
 * License: AGPLv3
 */
$(function(){
    function OrangePiZeroWiFiViewModel(parameters) {
        var self = this;

        self.loginState = parameters[0];
        self.settingsViewModel = parameters[1];

        self.pollingEnabled = false;
        self.pollingTimeoutId = undefined;

        self.editorWifiSsid = ko.observable();
        self.editorWifiPassphrase1 = ko.observable();
        self.editorWifiPassphrase2 = ko.observable();
        self.editorWifiPassphraseMismatch = ko.computed(function() {
            return self.editorWifiPassphrase1() != self.editorWifiPassphrase2();
        });

        self.working = ko.observable(false);
        self.error = ko.observable(false);
        
        self.Wifis = ko.observableArray([
            {ssid: "Hidden Wifi dummy"}
        ]);

        // initialize list helper

        self.getEntryId = function(data) {
            return "settings_plugin_orangepizero_wifi_" + md5(data.ssid);
        };

        self.refresh = function() {
            self.requestData();
        };

        self.fromResponse = function (response) {
            if (response.error !== undefined) {
                self.error(true);
                return;
            } else {
                self.error(false);
            }

            self.Wifis.removeAll();
            _.each(response.wifis, function(wifi) {
                self.Wifis.push({ ssid: wifi});
            });

            if (self.pollingEnabled) {
                self.pollingTimeoutId = setTimeout(function() {
                    self.requestData();
                }, 30000)
            }
        };

        self.configureWifi = function(data) {
            if (!self.loginState.isAdmin()) return;

            self.editorWifiSsid(undefined);
            self.editorWifiPassphrase1(undefined);
            self.editorWifiPassphrase2(undefined);
            $("#settings_plugin_orangepizero_wificonfig").modal("show");
        };

        self.confirmWifiConfiguration = function() {
            self.sendWifiConfig(self.editorWifiSsid(), self.editorWifiPassphrase1(), function() {
                self.Wifis.push({ ssid: self.editorWifiSsid()});
                self.editorWifi = undefined;
                self.editorWifiSsid(undefined);
                self.editorWifiPassphrase1(undefined);
                self.editorWifiPassphrase2(undefined);
                $("#settings_plugin_orangepizero_wificonfig").modal("hide");        
            });
        };

        self.sendWifiRefresh = function(force) {
            if (force === undefined) force = false;
            self._postCommand("list_ap", function(response) {
                self.fromResponse({wifis: response});
            });
        };

        self.sendWifiConfig = function(ssid, psk, successCallback, failureCallback) {
            if (!self.loginState.isAdmin()) return;

            self.working(true);
            
            self._postCommand("add_ap", {ap_name: ssid, ap_psk: psk=""}, successCallback, failureCallback, function() {
                self.working(false);
                if (self.reconnectInProgress) {
                    self.tryReconnect();
                }
            }, 5000);
        };

        self.sendForgetWifi = function(ssid) {
            if (!self.loginState.isAdmin()) return;
            
            self.Wifis.remove(this);
            
            self._postCommand("del_ap", {ap_name: ssid.ssid});
            

        };

        self._postCommand = function (command, data, successCallback, failureCallback, alwaysCallback, timeout) {
            var payload = _.extend(data, {command: command});

            var params = {
                url: API_BASEURL + "plugin/orangepizerowifi",
                type: "POST",
                dataType: "json",
                data: JSON.stringify(payload),
                contentType: "application/json; charset=UTF-8",
                success: function(response) {
                    if (successCallback) successCallback(response);
                },
                error: function() {
                    if (failureCallback) failureCallback();
                },
                complete: function() {
                    if (alwaysCallback) alwaysCallback();
                }
            };

            if (timeout != undefined) {
                params.timeout = timeout;
            }

            $.ajax(params);
        };

        self.requestData = function () {
            if (self.pollingTimeoutId != undefined) {
                clearTimeout(self.pollingTimeoutId);
                self.pollingTimeoutId = undefined;
            }

            $.ajax({
                url: API_BASEURL + "plugin/orangepizerowifi",
                type: "GET",
                dataType: "json",
                success: self.fromResponse
            });
        };

        self.onBeforeBinding = function() {
            self.settings = self.settingsViewModel.settings;
        };

        self.onSettingsShown = function() {
            self.pollingEnabled = true;
            self.requestData();
        };
    }
    
        OCTOPRINT_VIEWMODELS.push({
        construct: OrangePiZeroWiFiViewModel,
        additionalNames: ["orangePiZeroWiFiViewModel"],
        dependencies: ["loginStateViewModel", "settingsViewModel"],
        elements: ["#settings_plugin_orangepizero_dialog"]    
    });
});
