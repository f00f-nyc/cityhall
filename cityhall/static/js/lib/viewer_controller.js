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
        $scope.selected_env = 'auto';
        $scope.selected_value = '';

        $scope.rootForTree = function() {
            this.name = "/";
            this.override = "";
            this.valid = false;
            this.complete = false;
            this.value = "";
            this.path = "/";
            this.children = [];
            return this;
        };
        $scope.dataForTheTree = [ $scope.rootForTree() ];
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
            })
        };

        $scope.ViewEnv = function() {
            if ($scope.token) {
                $scope.selected_env = $scope.env;
                $scope.dataForTheTree = [ $scope.rootForTree() ];
                $scope.dataForTheTree[0].valid = true;
                $scope.Selected($scope.dataForTheTree[0]);
            }
        };

        $scope.CreateEnv = function() {
            if ($scope.token) {
                $http.post(
                    cityhall_url + 'auth/create/env/',
                    {name: $scope.env},
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

                var url = cityhall_url + 'env/view/' + $scope.selected_env + node.path + '?viewchildren=true';

                var req = {
                    method: 'GET',
                    url: url,
                    headers: {
                        'Auth-Token': $scope.token
                    }
                };

                $http(req).success(function (data) {
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
                            "override": child.override,
                            "valid": true,
                            "complete": child.override.length != 0,     // non-default overrides can't have children
                            "value": child.value,
                            "path": child.path,
                            "children": []
                        });
                    }
                }).error(function (data) {
                    node.children.push({
                        "name": "[ERROR]",
                        "override": "",
                        "valid": false,
                        "complete": true,
                        "value": "error with: " + url + ": " + data.toString(),
                        "path": "/",
                        "children": []
                    });
                });
            }

            $scope.selected_value = node.value;
            $scope.selected_node = node;
            $scope.selected_can_create = (node.override == '');
            $scope.selected_history = [];
        };

        $scope.Save = function() {
            var node = $scope.selected_node;
            var value = $scope.selected_value;
            var diff = value != node.value;

            if ($scope.token && diff) {

                var create_data = {
                    env: $scope.selected_env,
                    name: node.path,
                    value: value,
                    override: node.override
                };
                $http.post(cityhall_url+'env/create/', create_data, {headers: {'Auth-Token': $scope.token}})
                    .success(function (data) {
                        node.value = value;
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

            var create_data = {
                env: $scope.selected_env,
                name: $scope.selected_node.path + $scope.create_name,
                value: '',
                override: $scope.create_override
            };

            console.log('Create()     in create');
            console.log(create_data);

            $http.post(cityhall_url+'env/create/', create_data, {headers: {'Auth-Token': $scope.token}})
                    .success(function (data) {
                        console.log('Create()     created!');
                        $scope.selected_node.complete = false;
                        $scope.selected_node.children = [];
                        $scope.Selected($scope.selected_node, false);
                    });

            /* $scope.selected_node.children.push({

            });*/
        };

        $scope.UnsavedContent = function() {
            if ($scope.selected_value != $scope.selected_node.value) {
                return {background: 'lightpink'};
            }
            return {};
        };

        $scope.GetHistory = function() {
            if ($scope.token) {
                var url = cityhall_url+'env/view/'+$scope.selected_env+$scope.selected_node.path+
                    '?viewhistory=true&override='+$scope.selected_node.override;

                var req = {
                    method: 'GET',
                    url: url,
                    headers: {
                        'Auth-Token': $scope.token
                    }
                };

                $http(req).success(function (data){
                    $scope.selected_history = data.History;
                });
            }
        };

    }
]);