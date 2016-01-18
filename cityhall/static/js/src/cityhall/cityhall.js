angular.module('cityhall', ['angular-md5'])
.factory('settings', ['$http', 'md5',
    function(http, md5) {
        /**
         * Internal function.  Checks to see if func exists, and if it does,
         * call it using data.
         *
         * @param func - the function to call
         * @param err - the first parameter to pass to func
         * @param data - the second parameter to pass to func
         */
        var safeCall = function(func, err, data) {
            if ((func != undefined) && (func instanceof Function)) {
                func(err, data);
            }
        };

        var loggedIn = false;

        /**
         * Internal function.  Ensures that the user is logged in.
         * If he isn't, and he has passed through a failure() func, call
         * that. Otherwise, throw an exception to log in.
         *
         * @param failure - function to call with the error, if it exists
         * @returns {boolean} - true if logged in, false otherwise
         */
        var ensureLoggedIn = function(callback) {
            if (!loggedIn) {
                safeCall(callback, 'Not logged in, yet');
                return false;
            }
            return true;
        };

        /**
         * Internal function.  Returns a req object to be passed to http()
         *
         * @param method - the method to use 'GET', 'POST'
         * @param url - the url to use
         */
        var getReq = function(method, url) {
            return {
                method: method,
                url: url
            };
        };

        /**
         * Internal call to wrap a call to http and route response to success/failure
         *
         * @param req - the request to wrap
         * @param callback - the function to call when data comes back
         */
        var wrapHttpCall = function(req, callback) {
            http(req)
                .success(function (data) {
                    if (data['Response'] == 'Ok') {
                        safeCall(callback, undefined, data);
                    } else {
                        safeCall(callback, data, undefined);
                    }
                });
        };

        var getHashFromCleartext = function(password) {
            if (password.length > 0) {
                return md5.createHash(password);
            }

            return '';    //by convention, no password also gets no hash
        };

        return {
            isLoggedIn: function() { return loggedIn; },

            /**
             * This is the current logged in user, if you are logged in.
             */
            user_name: '',

            /**
             * This is the default environment for this session.
             * The calls to getVal() and getValOverride() will use this value.
             * The user should not, in regular usage, interact with this value.
             */
            environment: undefined,

            /**
             * The url for City Hall. Must be set this before calling login()
             *
             * Outside of setting it at start up, the user should not interact with this value.
             */
            url: '',

            /**
             * These are the permissions level for City Hall.  The intention is
             * for this to be used in conjunction with functions that deal with
             * user permissions (settings.grantUser(), settings.getUser(), etc)
             */
            Rights: {
                None: 0,
                Read: 1,
                ReadProtected: 2,
                Write: 3,
                Grant: 4
            },

            /**
             * This function logs into City Hall.
             *
             * It is required in order for anything to work, and should be the
             * first thing called.  It only has to be called once.
             *
             * @param user -the user name.
             * @param password - plaintext password.
             * @param callback - callback of the form `function (err, data)`
             */
            login: function(user, password, callback) {
                var self = this;

                if (!this.isLoggedIn()) {
                    var hash = getHashFromCleartext(password);
                    var auth_data = {'username': user, 'passhash': hash};
                    var auth_url = this.url + 'auth/';

                    http.post(auth_url, auth_data)
                        .success(function (data) {
                            if (data['Response'] == 'Ok') {
                                loggedIn = true;
                                self.user_name = user;
                                console.log('logged in for: ' + user);

                                self.getDefaultEnv(
                                    function(err, data) {
                                        if (err) { safeCall(callback, err); return; }

                                        self.environment = data['value'];
                                        console.log('default environment: ' + self.environment);
                                        safeCall(callback, undefined, data);
                                    }
                                );
                            } else {
                                safeCall(callback, data['Message']);
                            }
                        }).error(function (data) {
                            safeCall(callback, data);
                        });
                } else {
                    safeCall(callback, 'Already Logged in');
                }
            },

            logout: function(callback) {
                if (!ensureLoggedIn(callback)) { return; }

                var req = getReq('DELETE', this.url + 'auth/');
                var self = this;

                wrapHttpCall(req,
                    function (err, data) {
                        if (err) { safeCall(callback, err); return; }

                        loggedIn = false;
                        self.user_name = '';
                        self.environment = '';

                        safeCall(callback);
                    }
                );
            },

            /**
             * Returns the default environment for the current user.
             *
             * @param callback - callback of the form `function (err, data)`
             */
            getDefaultEnv: function(callback) {
                if (!ensureLoggedIn(callback)) { return; }

                var url = this.url + 'auth/user/' + this.user_name + '/default/';
                var req = getReq('GET', url);
                var self = this;
                wrapHttpCall(req,
                    function (err, data) {
                        if (err) { safeCall(callback, err); return; }

                        self.environment = data['value'];
                        safeCall(callback, undefined, data);
                    });
            },

            /**
             * This is a call to set the default environment.  If the user has
             * permissions, he can also update the /connect/[[user_name]] value
             * since that is what is read.
             *
             * @param default_env - the environment to set as default
             * @param callback - callback of the form `function (err, data)`
             */
            setDefaultEnv: function(default_env, callback) {
                if (!ensureLoggedIn(callback)) { return; }

                var url = this.url + 'auth/user/' + this.user_name + '/default/';
                var req = getReq('POST', url);
                req['data'] = {env: default_env};
                var self = this;
                wrapHttpCall(req,
                    function (err, data) {
                        if (err) { safeCall(callback, err); return; }

                        self.environment = default_env;
                        safeCall(callback, undefined, data);
                    });
            },

            /**
             * This is the call to explicitly get values, using a fully-qualified name.
             *
             * @param path - the path to get
             * @param env - the environment in which to look
             * @param override - the override to use.
             *      If this is undefined, the appropriate user default is retrieved
             * @param callback - callback of the form `function (err, data)`
             */
            get: function(path, env, override, callback) {
                if (!ensureLoggedIn(callback)) { return; }

                var get_url = this.url +'env/' + env + path;
                get_url += (override != undefined) ? '?override=' + override : '';
                var req = getReq('GET', get_url);
                wrapHttpCall(req, callback);
            },

            /**
             * This should be the most often used call to get a value.
             * This function gets the appropriate user default for a specific
             * path, and asynchronously updates obj['item'].
             *
             * @param path - the path to retrieve, will use the auto environment
             * @param obj - the object to update
             * @param item - the member of the object to actually be updated
             */
            getVal: function(path, obj, item) {
                return this.getValOverride(path, undefined, obj, item);
            },

            /** This should be the most often used call to get a value and override.
             * This function will asynchronously update obj['item']
             *
             * @param path - the path to retrieve, will use the auto environment
             * @param override - the override of the path to retrieve
             * @param obj - the object to update
             * @param item - the member of the object to actually be updated
             */
            getValOverride: function(path, override, obj, item) {
                this.get(path, this.environment, override,
                    function(err, data) {
                        if (err) {
                            console.log('An error occurred retrieving ' + path);
                            console.log(err);
                            return;
                        }

                        obj[item] = data['value'];
                    });
            },

            /**
             * This function will return all user rights
             *
             * @param user - the user to query for
             * @param callback - callback of the form `function (err, data)`
             */
            getUser: function(user, callback) {
                if (!ensureLoggedIn(callback)) { return; }

                var req = getReq('GET', this.url + 'auth/user/' + user);
                wrapHttpCall(req, callback);
            },

            /**
             * This function will return all of the children for a certain path.
             *
             * @param env - the environment to look in, if undefined, default
             * @param path - the path to search
             * @param callback - callback of the form `function (err, data)`
             */
            getChildren: function(env, path, callback) {
                if (!ensureLoggedIn(callback)) { return; }

                env = env == undefined ? this.environment : env;
                var get_url = this.url + 'env/' + env + path + '?viewchildren=true';
                var req = getReq('GET', get_url);
                wrapHttpCall(req, callback);
            },

            /**
             * This is the call to save values, using fully-qualified names.
             * Since saveValue will both create and update, all you need to make
             * sure of when calling it is that the parent in the path exists.
             *
             * @param env - the environment where the value is
             * @param path - the path to the value.  The parent of this path
             * @param override - the override to save to, may not be undefined
             * @param value - value to save, this can be undefined if you only wish to set protect
             * @param protect - protect status, this can be undefined if you only wish to set value
             * @param callback - callback of the form `function (err, data)`
             */
            saveValue: function(env, path, override, value, protect, callback) {
                if (!ensureLoggedIn(callback)) { return; }

                var data = {};
                if (value != undefined) { data.value = value; }
                if (protect != undefined) { data.protect = protect ? true : false; }

                var post_url = this.url + 'env/' + env + path + '?override='+ override;
                var req = getReq('POST', post_url);
                req['data'] = data;
                wrapHttpCall(req, callback);
            },

            /**
             * This will create an environment.
             * When it succeeds, the user will be set to Grant permissions on it.
             *
             * @param env - the environment to create
             * @param callback - callback of the form `function (err, data)`
             */
            createEnvironment: function(env, callback) {
                if (!ensureLoggedIn(callback)) { return; }

                var req = getReq('POST', this.url + 'auth/env/' + env + '/');
                wrapHttpCall(req, callback);
            },

            /**
             * This is will return the history of the key.
             *
             * @param env - environment to query
             * @param path - path within the environment
             * @param override - override for the path, this is required
             * @param callback - callback of the form `function (err, data)`
             */
            getHistory: function(env, path, override, callback) {
                if (!ensureLoggedIn(callback)) { return; }

                var url = this.url + 'env/' + env + path + '?override=' + override + '&viewhistory=true';
                var req = getReq('GET', url);
                wrapHttpCall(req, callback);
            },

            /**
             * This will delete a value, using a fully qualified name
             * @param env - the environment for this key
             * @param path - the path for this key
             * @param override - the override for this key, this is required
             * @param callback - callback of the form `function (err, data)`
             */
            delete: function(env, path, override, callback) {
                if (!ensureLoggedIn(callback)) { return; }

                var url = this.url + 'env/' + env + path + '?override=' + override;
                var req = getReq('DELETE', url);
                wrapHttpCall(req, callback);
            },

            /**
             * This function will create a user.
             * Since permissions are ad-hoc, any user can always create another.
             * As of version 1.0, a user does not automatically get read
             * permissions to the 'auto' environment, those have to be granted
             * explicitly.
             *
             * @param user - the new user to be created
             * @param password - the plaintext password for the new user
             * @param callback - callback of the form `function (err, data)`
             */
            createUser: function(user, password, callback) {
                if (!ensureLoggedIn(callback)) { return; }

                var hash = getHashFromCleartext(password);
                var create_url = this.url + 'auth/user/' + user + '/';
                req = getReq('POST', create_url);
                req['data'] = {'passhash': hash};
                wrapHttpCall(req, callback);
            },

            /**
             * This function will grant a user permissions to an environment
             *
             * @param user - the user to which to grant rights
             * @param env - the environment on which rights will be granted
             * @param rights - a value from this.Rights
             * @param callback - callback of the form `function (err, data)`
             */
            grantUser: function(user, env, rights, callback) {
                if (!ensureLoggedIn(callback)) { return; }

                var url = cityhall_url + 'auth/grant/';
                var req = getReq('POST', url);
                req['data'] = {'env': env, 'user': user, 'rights': rights};
                wrapHttpCall(req, callback);
            },

            /**
             * This function will delete a user.
             *
             * @param user - the user to delete
             * @param callback - callback of the form `function (err, data)`
             */
            deleteUser: function(user, callback) {
                if (!ensureLoggedIn(callback)) { return; }

                var delete_url = this.url + 'auth/user/' + user + '/';
                var req = getReq('DELETE', delete_url);
                wrapHttpCall(req, callback);
            },

            /**
             * This function will get all users for a particular environment.
             * If a user's rights are greater than this.Rights.None, that
             * user will be listed here.
             *
             * @param env - the environment to query
             * @param callback - callback of the form `function (err, data)`
             */
            viewUsers: function(env, callback) {
                if (!ensureLoggedIn(callback)) { return; }

                var users_url = this.url + 'auth/env/' + env + '/';
                var req = getReq('GET', users_url);
                wrapHttpCall(req, callback);
            },

            /**
             * This function will update the current logged in user's password
             *
             * @param password - the plaintext password to update to
             * @param callback - callback of the form `function (err, data)`
             */
            updatePassword: function(password, callback) {
                if (!ensureLoggedIn(callback)) { return; }

                var delete_url = this.url + 'auth/user/' + this.user_name + '/';
                var req = getReq('PUT', delete_url);
                req.data = {'passhash': getHashFromCleartext(password)};
                wrapHttpCall(req, callback);
            }
        };
    }
]);