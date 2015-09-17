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

app.controller('CityHallCtrl', ['$scope', 'md5', 'settings',
    function($scope, md5, settings) {
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
                real_path: '',
                env: '',
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
        $scope.loggedIn = false;

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

        $scope.default_env = '';
        $scope.prev_default_env = '';

        $scope.Login = function() {
            var error = function(data) {
                $scope.loggedIn = false;
                $scope.status = 'Failed to login for: ' + $scope.user;
                console.log(data);
                if (data.Message != undefined) {
                    alert(data.Message);
                } else {
                    alert(data);
                }
            };

            settings.url = cityhall_url;
            settings.login($scope.user, $scope.pass,
                function(data) {
                    $scope.loggedIn = true;
                    $scope.status = data['Response'];
                    $scope.prev_default_env =  $scope.default_env = settings.environment;
                    $scope.pass = '';
                    $scope.dataForTheTree[0].valid = true;

                    settings.getUser($scope.user,
                        function (data) {
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
                                    children: [],
                                    parent: null,
                                    order: order,
                                    env: env,
                                    real_path: '/'
                                });
                                order++;
                            }
                        },
                        error
                    );

                },
                error
            );

            //TODO: implement an extra get override ?viewprotect=true to set protect status of root
        };

        $scope.Logout = function() {
            $scope.loggedIn = false;
            settings.loggedIn = false;
            settings.user_name = '';
            $scope.dataForTheTree = [{
                name: 'Not connected',
                real_name: '/',
                protect: false,
                override: '',
                valid: false,
                complete: false,
                value: '',
                real_path: '',
                env: '',
                children: [],
                parent: null,
                order: 0
            }];
            $scope.selected_node = $scope.dataForTheTree[0];
            $scope.selected_history = [];
            settings.environment = undefined;
            $scope.status = "Logged out";
        };

        $scope.CreateEnv = function() {
            settings.createEnvironment($scope.env,
                function (data) {
                    $scope.UnloadEnv('users');
                    alert(data.Message);
                },
                function (data) {
                    alert(data.Message);
                }
            );
        };

        $scope.Selected = function(node, expanded) {
            if (node.valid && $scope.loggedIn && !node.complete) {
                node.complete = true;

                settings
                    .getChildren(node.env, node.real_path,
                        function success(data) {
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
                                    "env": node.env,
                                    "real_path": child.path,
                                    "children": [],
                                    "parent": node,
                                    "protect": child.protect
                                });
                            }
                        },
                        function failure(data) {
                            node.children.push({
                                "name": "[ERROR]",
                                "real_name": "",
                                "override": "",
                                "valid": false,
                                "complete": true,
                                "value": "error with: " + node.env + node.real_path + ": " + data.toString(),
                                "real_path": "/",
                                "env": node.env,
                                "children": [],
                                "parent": node,
                                "protect": false
                        }
                    );
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
            var value = ($scope.selected_value != node.value) ? $scope.selected_value : undefined;
            var protect = ($scope.selected_protected != node.protect) ? $scope.selected_protected : undefined;

            if ($scope.loggedIn && (value || protect)) {
                settings.saveValue(node.env, node.real_path, node.override, value, protect,
                    function() {
                        node.value = $scope.selected_value;
                        node.protect = $scope.selected_protected;
                    },
                    function(data) {
                        alert(data['Message']);
                    }
                );
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

            if (!$scope.loggedIn || !$scope.selected_can_create) {
                return;
            }

            var node = $scope.selected_node;
            settings.saveValue(node.env, node.real_path + $scope.create_name, $scope.create_override, '', false,
                function(data) {
                    node.complete = false;
                    node.children = [];
                    $scope.Selected(node, false);
                },
                function(data) {
                    alert('Create value failed: ' + data.Message);
                }
            );
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
            var node = $scope.selected_node;
            settings.getHistory(
                node.env, node.real_path, node.override,
                function (data) {
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
                },
                function(data) {
                    alert('Get History failed: ' + data.Message);
                }
            );
        };

        $scope.Delete = function() {
            var node = $scope.selected_node;
            settings.delete(node.env, node.real_path, node.override,
                function(data) {
                    var should_remove = function(current) {
                        if (current.real_name == node.real_name) {
                            if (node.override == '') {
                                // if deleting a global, must delete all overrides, too
                                return true;
                            } else if (current.override == node.override) {
                                // otherwise, we only want to match the override node
                                return true;
                            }
                        }

                        return false;
                    };

                    var parent = node.parent;
                    var i=0;

                    while (i < parent.children.length) {
                        if (should_remove(parent.children[i])) {
                            parent.children.splice(i, 1);
                        } else {
                            i++;
                        }
                    }

                    $scope.Selected(parent);
                },
                function(data) {
                    alert('Delete key failed: ' + data.Message);
                }
            );
        };

        $scope.UnloadEnv = function(env) {
            var unload_env_in = function(arr) {
                for (var i=0; i<arr.length; i++) {
                    var node = arr[i];
                    if (node.real_name == env) {
                        node.name = node.real_name + INCOMPLETE_MARKER;
                        node.children = [];
                        node.complete = false;
                    }
                }
            };

            unload_env_in($scope.dataForTheTree);
            unload_env_in($scope.hiddenDataForTheTree);
        };

        $scope.MoveKey = function() {
            var node = $scope.selected_node;

            if (node.real_path == '/') {
                alert("Cannot move root");
                return;
            }
            if ($scope.move_key_env.length == 0) {
                alert("Must enter a environment name");
                return;
            }
            if (node['env'] === $scope.move_key_env) {
                alert("Cannot move to the current environment");
                return;
            }

            var env_from = node.env;
            var env_to = $scope.move_key_env;
            var unloadEnv = this.UnloadEnv;
            var move = function(path, override, children) {
                settings.get(path, env_from, override,
                    function(data) {
                        settings.saveValue(
                            env_to, path, override, data['value'], data['protect'],
                            function(data) {
                                $scope.view_mode = 1;
                            },
                            function(data) {
                                throw "Unable to set value for " + env_from + path + ": " + data['Message'];
                            });
                        unloadEnv(env_to);
                    },
                    function(data) {
                        throw 'Unable to get value for ' + env_from + path +': ' + data['Message'];
                    }
                );

                if (children && (override == '')) {
                    settings.getChildren(env_from, path,
                        function(data) {
                            for (var i=0; i<data.children.length; i++) {
                                var child = data.children[i];
                                move(child.path, child.override, children);
                            }
                        },
                        function (data) {
                            throw "error while attempting to move subkeys of: " + path + ': ' + data['Message'];
                        });
                }
            };

            move(node.real_path, node.override, $scope.move_key_sub);
        };

        $scope.CreateUser = function() {
            settings.createUser($scope.create_user, $scope.create_pass,
                function (data) {
                    $scope.UnloadEnv('users');
                    alert('User ' + $scope.create_user + ' created successfully');
                },
                function (data) {
                    alert('Failed to crate user: ' + data.Message);
                }
            );
        };

        $scope.DeleteUser = function() {
            settings.deleteUser($scope.delete_user,
                function (data) {
                    $scope.UnloadEnv('users');
                    alert('User ' + $scope.delete_user + ' deleted successfully.');
                },
                function(data) {
                    alert('Failed to delete user ' + $scope.delete_user + ': ' + data.Message);
                }
            );
        };

        $scope.GrantUser = function() {
            settings.grantUser($scope.grant_user, $scope.grant_env, $scope.grant_rights,
                function(data) {
                    $scope.UnloadEnv('users');
                    alert(data['Message']);
                },
                function(data) {
                    alert('Failed to grant rights: ' + data['Message']);
                }
            );
        };

        $scope.ViewUsers = function() {
            var int_to_str = function(int) {
                    switch (int){
                        case "0":
                        case 0: return "None";
                        case "1":
                        case 1: return "Read";
                        case "2":
                        case 2: return "Read Protected";
                        case "3":
                        case 3: return "Write";
                        case "4":
                        case 4: return "Grant";
                    }
                    return "Unknown";
                };
            settings.viewUsers($scope.view_env,
                function(data) {
                    $scope.view_users = [];
                    var users = data['Users'];

                    for (var env in users) {
                        $scope.view_users.push({
                            environment: env,
                            rights: int_to_str(users[env])
                        });
                    }
                },
                function(data) {
                    alert('Failed to view users: ' + data.Message);
                }
            );
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
        };

        $scope.UnsavedDefaultEnv = function() {
            if ($scope.default_env != $scope.prev_default_env) {
                return {background: 'lightpink'};
            }

            return {};
        };

        $scope.SetDefaultEnv = function() {
            settings.setDefaultEnv($scope.default_env,
                function () {
                    $scope.prev_default_env = $scope.default_env;
                    $scope.UnloadEnv('auto');
                },
                function(data) {
                    alert('Failed to set default environment: ' + data.Message);
                });
        };
    }
]);