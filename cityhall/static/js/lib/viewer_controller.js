/* Copyright 2015 Digital Borderlands Inc.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License, version 3,
 * as published by the Free Software Foundation.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

String.prototype.endsWith = function(suffix) {
    return this.indexOf(suffix, this.length - suffix.length) !== -1;
};

var INCOMPLETE_MARKER = "...";

app.controller('CityHallCtrl', ['$scope', 'md5', '$http',
    function($scope, md5, $http) {
        $scope.user = 'cityhall';
        $scope.pass = '';
        $scope.env = 'dev';
        $scope.selected_value = '';
        $scope.selected_protected = false;

        $scope.view_mode = 1;

        $scope.dataForTheTree = [{
            name: 'Not connected',
            real_name: '/',
            protect: false,
            override: '',
            valid: false,
            complete: false,
            value: '',
            path: '',
            children: [],
            parent: null,
            order: 0
        }];
        $scope.hiddenDataForTheTree = [];
        $scope.treeOptions = {
            nodeChildren: "children",
            dirSelectable: true,
            injectClasses: {
                ul: "a1",
                li: "a2",
                liSelected: "a7",
                iExpanded: "a3",
                iCollapsed: "a4",
                iLeaf: "a5",
                label: "a6",
                labelSelected: "a8"
            }
        };
        $scope.selected_node = $scope.dataForTheTree[0];
        $scope.selected_history = [];

        $scope.create_name = '';
        $scope.create_override = '';
        $scope.selected_can_create = true;

        $scope.status = 'Ready.';
        $scope.token = '';

        $scope.move_key_env = '';
        $scope.move_key_sub = false;

        $scope.create_user = '';
        $scope.create_pass = '';

        $scope.delete_user = '';

        $scope.grant_user = '';
        $scope.grant_rights = 1;
        $scope.grant_env = '';

        $scope.view_env = '';
        $scope.view_users = [];

        $scope.env_search = '';

        $scope.urlForPath = function(path, override) {
            var url = cityhall_url + 'env/' + path;
            if (override == undefined) {
                return url;
            }
            return url + '?override=' + override;
        };

        $scope.urlForNode = function(node) {
            return $scope.urlForPath(node.path);
        };

        $scope.EnvFromNode = function(node) {
            while (node.parent != null) {
                return $scope.EnvFromNode(node.parent);
            };

            return node.real_name;
        };

        $scope.Login = function() {
            var hash = '';
            if ($scope.pass.length > 0) {
                hash = md5.createHash($scope.pass);
            }

            var auth_data = {'username': $scope.user, 'passhash': hash};
            var auth_url = cityhall_url + 'auth/';
            $http.post(auth_url, auth_data).success(function (data){
                $scope.token = data['Token'];
                $scope.status = data['Response'];
                $scope.dataForTheTree[0].valid = true;

                var req = {
                    method: 'GET',
                    url: cityhall_url + 'auth/user/' + $scope.user + '/',
                    headers: {
                        'Auth-Token': $scope.token
                    }
                };

                $http(req).success(function (data) {
                    $scope.dataForTheTree = [];
                    var order = 0;

                    for (var env in data['Environments']) {
                        $scope.dataForTheTree.push({
                            name: env + INCOMPLETE_MARKER,
                            real_name: env,
                            protect: false,
                            override: '',
                            valid: true,
                            complete: false,
                            value: '',
                            path: env + '/',
                            children: [],
                            parent: null,
                            order: order
                        });
                        order++;
                    }
                });
            });

            //TODO: implement an extra get override ?viewprotect=true to set protect status of root
        };

        $scope.CreateEnv = function() {
            if ($scope.token) {
                $http.post(
                    cityhall_url + 'auth/env/' + $scope.env + '/',
                    {},
                    {headers: {'Auth-Token': $scope.token}}
                )
                .success(function (data) {
                        console.log(data);
                        alert(data.Message);
                    });
            }
        };

        $scope.Selected = function(node, expanded) {
            if (node.valid && $scope.token && !node.complete) {
                node.complete = true;

                var url = $scope.urlForNode(node) + '?viewchildren=true';

                var req = {
                    method: 'GET',
                    url: url,
                    headers: {
                        'Auth-Token': $scope.token
                    }
                };

                $http(req).success(function (data) {
                    console.log(data);

                    if (node.name.endsWith(INCOMPLETE_MARKER)) {
                        node.name = node.name.substring(0, node.name.length-3);
                    }

                    for (var i = 0; i < data.children.length; i++) {
                        var child = data.children[i];
                        var node_name = child.name;
                        if (child.override.length > 0) {
                            node_name = node_name + " [" + child.override + "]";
                        } else {
                            node_name = node_name + INCOMPLETE_MARKER;
                        }

                        node.children.push({
                            "name": node_name,
                            "real_name": child.name,
                            "override": child.override,
                            "valid": true,
                            "complete": child.override.length != 0,     // non-default overrides can't have children
                            "value": child.value,
                            "path": $scope.EnvFromNode(node) + child.path,
                            "children": [],
                            "parent": node,
                            "protect": child.protect
                        });

                        console.log($scope.EnvFromNode(node) + child.path);
                    }
                }).error(function (data) {
                    node.children.push({
                        "name": "[ERROR]",
                        "real_name": "",
                        "override": "",
                        "valid": false,
                        "complete": true,
                        "value": "error with: " + url + ": " + data.toString(),
                        "path": "/",
                        "children": [],
                        "parent": node,
                        "protect": false
                    });
                });
            }

            $scope.selected_value = node.value;
            $scope.selected_protected = node.protect;
            $scope.selected_node = node;
            $scope.selected_can_create = (node.override == '');
            $scope.selected_history = [];
        };

        $scope.Save = function() {
            var node = $scope.selected_node;
            var diff = false;

            var data = {};
            if ($scope.selected_value != node.value) {
                data.value = $scope.selected_value;
                diff = true;
            }
            if ($scope.selected_protected != node.protect) {
                data.protect = $scope.selected_protected;
                diff = true;
            }

            if ($scope.token && diff) {
                var url = $scope.urlForNode(node) + '?override=' + node.override;
                $http.post(url, data, {headers: {'Auth-Token': $scope.token}})
                    .success(function (data) {
                        node.value = $scope.selected_value;
                        node.protect = $scope.selected_protected;
                    });
            }
        };

        $scope.Create = function() {
            if ($scope.create_name == undefined) {
                alert('Cannot use these characters: / \' " <tab> <carriage return> <newline>');
                return;
            }

            if ($scope.create_name.length == 0) {
                alert('Must specify a name');
                return;
            }

            if ($scope.create_override == undefined) {
                alert('Override should be the name of a user');
                return;
            }

            if (!$scope.token || !$scope.selected_can_create) {
                return;
            }

            var url = $scope.urlForPath($scope.selected_node.path + $scope.create_name, $scope.create_override);

            console.log('Create()     in create for: ' + url);

            $http.post(url, {value: ''}, {headers: {'Auth-Token': $scope.token}})
                    .success(function (data) {
                        console.log('Create()     created!');
                        $scope.selected_node.complete = false;
                        $scope.selected_node.children = [];
                        $scope.Selected($scope.selected_node, false);
                    });
        };

        $scope.UnsavedContent = function() {
            if (($scope.selected_value != $scope.selected_node.value)  ||
                ($scope.selected_protected != $scope.selected_node.protect)) {
                return {background: 'lightpink'};
            }

            return {};
        };

        $scope.GetHistory = function() {
            $scope.view_mode = 3;

            if ($scope.token) {
                var url = $scope.urlForPath($scope.selected_node.path, $scope.selected_node.override);
                url = url + '&viewhistory=true';

                var req = {
                    method: 'GET',
                    url: url,
                    headers: {
                        'Auth-Token': $scope.token
                    }
                };

                $http(req).success(function (data){
                    var first = data.History[0];
                    $scope.selected_history = [
                        {
                            datetime: first.datetime,
                            author: first.author,
                            type: "Created: " + first.name,
                            value: first.value,
                            public: (first.protect > 0) ? "N" : "Y"
                        }
                    ];
                    var exists = new Array();
                    var last_name = first.name;
                    var last_parent = first.parent;
                    var key_id = first.id;

                    for (var i=1; i<data.History.length; i++) {
                        var current = data.History[i];
                        var type = "Value changed";

                        if (current.id == key_id) {
                            if (current.name != last_name) {
                                type = "Renamed: " + current.name;
                                last_name = current.name;
                            }
                            else if (current.parent != last_parent) {
                                type = "Key moved";
                                last_parent = current.parent;
                            }
                        }
                        else {
                            var id = "id" + current.id;
                            var child_name = current.name;
                            if (current.override != "") {
                                child_name = current.name + " [" + current.override + "]";
                            }

                            if (exists[id] == undefined) {
                                type = "Created: " + child_name;
                                exists[id] = true;
                            } else {
                                type = "Deleted: " + child_name;
                                delete exists[id];
                            }
                        }

                        $scope.selected_history.push({
                                datetime: current.datetime,
                                author: current.author,
                                type: type,
                                value: current.value,
                                public: (current.protect > 0) ? "N" : "Y"
                            })
                    }
                });
            }
        };

        $scope.Delete = function() {
            if ($scope.token) {
                var url = $scope.urlForPath($scope.selected_node.path, $scope.selected_node.override);

                var req = {
                    method: 'DELETE',
                    url: url,
                    headers: {
                        'Auth-Token': $scope.token
                    }
                };

                $http(req).success(function (data) {
                    var current = $scope.selected_node;

                    var should_delete = function(node) {
                        if (current.real_name == node.real_name) {
                            if (current.override == '') {
                                return true;
                            } else if (current.override == node.override) {
                                return true;
                            }
                        }

                        return false;
                    };

                    var parent = current.parent;
                    var i=0;

                    while (i < parent.children.length) {
                        if (should_delete(parent.children[i])) {
                            parent.children.splice(i, 1);
                        } else {
                            i++;
                        }
                    }

                    $scope.Selected(parent);
                });
            }
        };

        $scope.MoveKey = function() {
            var node = $scope.selected_node;

            if (node.path == '/') {
                alert("Cannot move root");
                return;
            }
            if ($scope.move_key_env.length == 0) {
                alert("Must enter a environment name");
                return;
            }
            if ($scope.EnvFromNode(node) === $scope.move_key_env) {
                alert("Cannot move to the current environment");
                return;
            }
            if ($scope.move_key_sub) {
                alert("Moving children not implemented yet");
            }

            var switchPath = function(path, env) {
                return env + path.substring(path.indexOf('/'));
            };

            var new_parent_path = switchPath($scope.selected_node.parent.path, $scope.move_key_env);
            var url =  $scope.urlForPath(new_parent_path);

            var req = {
                    method: 'GET',
                    url: url,
                    headers: {
                        'Auth-Token': $scope.token
                    }
                };

            $http(req).success(function (data) {
                if (data.Response == 'Failure') {
                    alert(data.Message);
                    return;
                }

                var new_path = switchPath($scope.selected_node.path, $scope.move_key_env);
                url = $scope.urlForPath(new_path, node.override);
                var data = {
                    value: node.value,
                    protect: node.protect
                };

                $http.post(url, data, {headers: {'Auth-Token': $scope.token}})
                    .success(function (data) {
                        var unload_env_in = function(arr) {
                            for (var i=0; i<arr.length; i++) {
                                var node = arr[i];
                                if (node.real_name == $scope.move_key_env) {
                                    node.name = node.real_name + INCOMPLETE_MARKER;
                                    node.children = [];
                                    node.complete = false;
                                }
                            }
                        };

                        unload_env_in($scope.dataForTheTree);
                        unload_env_in($scope.hiddenDataForTheTree);
                    })

                }).error(function (data) {
                    alert('Unable to move to ' + $scope.move_key_env + $scope.selected_node.path +
                    ', the environment or the parent path do not exist.');
                });
        };

        $scope.CreateUser = function() {
            var hash = '';
            if ($scope.create_pass.length > 0) {
                hash = md5.createHash($scope.create_pass);
            }

            var create_data = {'passhash': hash};
            var create_url = cityhall_url + 'auth/user/' + $scope.create_user + '/' ;
            $http.post(create_url, create_data, {headers: {'Auth-Token': $scope.token}})
                .success(function (data){
                    console.log(data);
                    if (data.Response == 'Failure') {
                        alert(data.Message);
                    } else {
                        alert('User ' + $scope.create_user + ' created successfully.');
                    }
                });
        };

        $scope.DeleteUser = function() {
            if ($scope.token) {
                var req = {
                    method: 'DELETE',
                    url: cityhall_url + 'auth/user/' + $scope.delete_user + '/',
                    headers: {
                        'Auth-Token': $scope.token
                    }
                };

                $http(req).success(function (data) {
                    if (data.Response == 'Failure') {
                        alert(data.Message);
                    }
                    else {
                        alert('User ' + $scope.delete_user + ' deleted successfully.')
                    }
                });
            }
        };

        $scope.GrantUser = function() {
            if ($scope.token) {
                var url = cityhall_url + 'auth/grant/';
                var data = {'env': $scope.grant_env, 'user': $scope.grant_user, 'rights': $scope.grant_rights};
                $http.post(url, data, {headers: {'Auth-Token': $scope.token}})
                    .success(function (data) {
                        alert(data['Message']);
                    });
            }
        };

        $scope.ViewUsers = function() {
            if ($scope.token) {
                var int_to_str = function(int) {
                    switch (int){
                        case 0: return "None";
                        case 1: return "Read";
                        case 2: return "Read Protected";
                        case 3: return "Write";
                        case 4: return "Grant";
                        case 5: return "Admin";
                    }
                    return "Unknown";
                };
                $scope.view_users = [];

                var url = cityhall_url + 'auth/env/' + $scope.view_env + '/';

                var req = {
                    method: 'GET',
                    url: url,
                    headers: {
                        'Auth-Token': $scope.token
                    }
                };

                $http(req).success(function (data) {
                    console.log(data);

                    if (data['Response'] == 'Ok') {
                        var users = data['Users'];

                        for (var env in users) {
                            $scope.view_users.push({
                                environment: env,
                                rights: int_to_str(users[env])
                            });
                        }
                    } else {
                        alert(data['Message']);
                    }
                });
            }
        };

        $scope.EnvSearch = function() {
            var allData = $scope.hiddenDataForTheTree;
            for (var i=0; i<$scope.dataForTheTree.length; i++) {
                allData.push($scope.dataForTheTree[i]);
            }
            allData.sort(function(node1, node2) { return node1.order-node2.order; });

            $scope.hiddenDataForTheTree = [];
            $scope.dataForTheTree = [];

            for (i=0; i<allData.length; i++) {
                var node = allData[i];
                if (node.real_name.indexOf($scope.env_search) > -1) {
                    $scope.dataForTheTree.push(node);
                } else {
                    $scope.hiddenDataForTheTree.push(node);
                }
            }
        }
    }
]);