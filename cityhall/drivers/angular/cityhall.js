angular.module('cityhall', ['angular-md5'])
.factory('settings', ['$http', 'md5',
    function(http, md5) {
        return {
            loggedIn: false,

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
             * Internal function.  Checks to see if func exists, and if it does,
             * call it using data.
             *
             * @param func - the function to call
             * @param data - the data to pass to the
             */
            safeCall: function(func, data) {
                if ((func != undefined) && (func instanceof Function)) {
                    func(data);
                }
            },

            /**
             * Internal function.  Ensures that the user is logged in.
             * If he isn't, and he has passed through a failure() func, call
             * that. Otherwise, throw an exception to log in.
             *
             * @param failure - function to call with the error, if it exists
             * @returns {boolean} - true if logged in, false otherwise
             */
            ensureLoggedIn: function(failure) {
                if (!this.loggedIn) {
                    if ((failure != undefined) && (failure instanceof Function)) {
                        failure({Response: 'Failure', Message: 'Not logged in, yet.'});
                    } else {
                        throw 'Not logged in, yet';
                    }

                    return false;
                }
                return true;
            },

            /**
             * Internal function.  Returns a req object to be passed to http()
             *
             * @param method - the method to use 'GET', 'POST'
             * @param url - the url to use
             */
            getReq: function(method, url) {
                return {
                    method: method,
                    url: url
                };
            },

            /**
             * Internal call to wrap a call to http and route response to success/failure
             *
             * @param req - the request to wrap
             * @param success - the function to call on success
             * @param failure - the function to call on failure
             */
            wrapHttpCall: function(req, success, failure, data) {
                safeCallRef = this.safeCall;
                http(req)
                    .success(function (data) {
                        if (data['Response'] == 'Ok') {
                            safeCallRef(success, data);
                        } else {
                            safeCallRef(failure, data);
                        }
                    });
            },

            getHashFromCleartext: function(password) {
                if (password.length > 0) {
                    return md5.createHash(password);
                }

                return '';    //by convention, no password also gets no hash
            },

            /**
             * This function logs into City Hall.
             *
             * It is required in order for anything to work, and should be the
             * first thing called.  It only has to be called once.
             *
             * @param user -the user name.
             * @param password - plaintext password.
             * @param success - optional function to execute on success.
             * @param failure - optional function to execute on failure.
             */
            login: function(user, password, success, failure) {
                var self = this;

                if (!this.loggedIn) {
                    var hash = this.getHashFromCleartext(password);
                    var auth_data = {'username': user, 'passhash': hash};
                    var auth_url = this.url + 'auth/';

                    http.post(auth_url, auth_data)
                        .success(function (data) {
                            if (data['Response'] == 'Ok') {
                                self.loggedIn = true;
                                self.user_name = user;
                                console.log('logged in for: ' + user);

                                self.getDefaultEnv(
                                    function(data) {
                                        self.environment = data['value'];
                                        console.log('default environment: ' + self.environment);
                                        self.safeCall(success, data);
                                    },
                                    failure
                                );
                            } else {
                                self.safeCall(failure, data['Message']);
                            }
                        }).error(function (data) {
                            self.safeCall(failure, data);
                        });
                } else {
                    this.safeCall(failure, 'Already Logged in');
                }
            },

            logout: function(success, failure) {
                if (!this.ensureLoggedIn(failure)) { return; }

                var req = this.getReq('DELETE', this.url + 'auth/');
                var self = this;

                this.wrapHttpCall(req,
                    function (data) {
                        self.loggedIn = false;
                        self.user_name = '';
                        self.environment = '';

                        success(data);
                    },
                    failure
                );
            },

            /**
             * Returns the default environment for the current user.
             *
             * @param success - optional function to execute on success.
             * @param failure - optional function to execute on failure.
             */
            getDefaultEnv: function(success, failure) {
                if (!this.ensureLoggedIn(failure)) { return; }

                var url = this.url + 'auth/user/' + this.user_name + '/default/';
                var req = this.getReq('GET', url);
                var self = this;
                this.wrapHttpCall(req,
                    function (data) {
                        self.environment = data['value'];
                        success(data);
                    },
                    failure);
            },

            /**
             * This is a call to set the default environment.  If the user has
             * permissions, he can also update the /connect/[[user_name]] value
             * since that is what is read.
             *
             * @param default_env - the environment to set as default
             * @param success - optional function to execute on success.
             * @param failure - optional function to execute on failure.
             */
            setDefaultEnv: function(default_env, success, failure) {
                if (!this.ensureLoggedIn(failure)) { return; }

                var url = this.url + 'auth/user/' + this.user_name + '/default/';
                var req = this.getReq('POST', url);
                req['data'] = {env: default_env};
                var self = this;
                this.wrapHttpCall(req,
                    function (data) {
                        self.environment = default_env;
                        success(data);
                    },
                    failure);
            },

            /**
             * This is the call to explicitly get values, using a fully-qualified name.
             *
             * @param path - the path to get
             * @param env - the environment in which to look
             * @param override - the override to use.
             *      If this is undefined, the appropriate user default is retrieved
             * @param success - function to call on success
             * @param failure - function to call on failure
             */
            get: function(path, env, override, success, failure) {
                if (!this.ensureLoggedIn(failure)) { return; }

                var get_url = this.url +'env/' + env + path;
                get_url += (override != undefined) ? '?override=' + override : '';
                var req = this.getReq('GET', get_url);
                this.wrapHttpCall(req, success, failure);
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
                this.get(path, this.environment, undefined,
                function(data) {
                    obj[item] = data['value'];
                },
                function(data) {
                    console.log('An error occurred retrieving ' + path);
                    console.log(data);
                });
            },

            /**
             * This function will return all user rights
             *
             * @param user - the user to query for
             * @param success - function to call on success
             * @param failure - function to call on failure
             */
            getUser: function(user, success, failure) {
                if (!this.ensureLoggedIn(failure)) { return; }
                var req = this.getReq('GET', this.url + 'auth/user/' + user);
                this.wrapHttpCall(req, success, failure);
            },

            /**
             * This function will return all of the children for a certain path.
             *
             * @param env - the environment to look in, if undefined, default
             * @param path - the path to search
             * @param success - function to call on success
             * @param failure - function to call on failure
             */
            getChildren: function(env, path, success, failure) {
                if (!this.ensureLoggedIn(failure)) { return; }

                env = env == undefined ? this.environment : env;
                var get_url = this.url + 'env/' + env + path + '?viewchildren=true';
                var req = this.getReq('GET', get_url);
                this.wrapHttpCall(req, success, failure);
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
             * @param success - function to call on success
             * @param failure - function to call on failure
             */
            saveValue: function(env, path, override, value, protect, success, failure) {
                if (!this.ensureLoggedIn(failure)) { return; }

                var data = {};
                if (value != undefined) { data.value = value; }
                if (protect != undefined) { data.protect = protect ? true : false; }

                var post_url = this.url + 'env/' + env + path + '?override='+ override;
                var req = this.getReq('POST', post_url);
                req['data'] = data;
                this.wrapHttpCall(req, success, failure);
            },

            /**
             * This will create an environment.
             * When it succeeds, the user will be set to Grant permissions on it.
             *
             * @param env - the environment to create
             * @param success - function to call on success
             * @param failure - function to call on failure
             */
            createEnvironment: function(env, success, failure) {
                if (!this.ensureLoggedIn(failure)) { return; }

                var req = this.getReq('POST', this.url + 'auth/env/' + env + '/');
                this.wrapHttpCall(req, success, failure);
            },

            /**
             * This is will return the history of the key.
             *
             * @param env - environment to query
             * @param path - path within the environment
             * @param override - override for the path, this is required
             * @param success - function to call on success
             * @param failure - function to call on failure
             */
            getHistory: function(env, path, override, success, failure) {
                if (!this.ensureLoggedIn(failure)) { return; }

                var url = this.url + 'env/' + env + path + '?override=' + override + '&viewhistory=true';
                var req = this.getReq('GET', url);
                this.wrapHttpCall(req, success, failure);
            },

            /**
             * This will delete a value, using a fully qualified name
             * @param env - the environment for this key
             * @param path - the path for this key
             * @param override - the override for this key, this is required
             * @param success - function to call on success
             * @param failure - function to call on failure
             */
            delete: function(env, path, override, success, failure) {
                if (!this.ensureLoggedIn(failure)) { return; }

                var url = this.url + 'env/' + env + path + '?override=' + override;
                var req = this.getReq('DELETE', url);
                this.wrapHttpCall(req, success, failure);
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
             * @param success - function to call on success
             * @param failure - function to call on failure
             */
            createUser: function(user, password, success, failure) {
                if (!this.ensureLoggedIn(failure)) { return; }

                var hash = this.getHashFromCleartext(password);
                var create_url = this.url + 'auth/user/' + user + '/';
                req = this.getReq('POST', create_url);
                req['data'] = {'passhash': hash};
                this.wrapHttpCall(req, success, failure);
            },

            /**
             * This function will grant a user permissions to an environment
             *
             * @param user - the user to which to grant rights
             * @param env - the environment on which rights will be granted
             * @param rights - a value from this.Rights
             * @param success - function to call on success
             * @param failure - function to call on failure
             */
            grantUser: function(user, env, rights, success, failure) {
                if (!this.ensureLoggedIn(failure)) { return; }

                var url = cityhall_url + 'auth/grant/';
                var req = this.getReq('POST', url);
                req['data'] = {'env': env, 'user': user, 'rights': rights};
                this.wrapHttpCall(req, success, failure);
            },

            /**
             * This function will delete a user.
             *
             * @param user - the user to delete
             * @param success - function to call on success
             * @param failure - function to call on failure
             */
            deleteUser: function(user, success, failure) {
                if (!this.ensureLoggedIn(failure)) { return; }

                var delete_url = this.url + 'auth/user/' + user + '/';
                var req = this.getReq('DELETE', delete_url);
                this.wrapHttpCall(req, success, failure);
            },

            /**
             * This function will get all users for a particular environment.
             * If a user's rights are greater than this.Rights.None, that
             * user will be listed here.
             *
             * @param env - the environment to query
             * @param success - function to call on success
             * @param failure - function to call on failure
             */
            viewUsers: function(env, success, failure) {
                if (!this.ensureLoggedIn(failure)) { return; }

                var users_url = this.url + 'auth/env/' + env + '/';
                var req = this.getReq('GET', users_url);
                this.wrapHttpCall(req, success, failure);
            },

            updatePassword: function(password, success, failure) {
                if (!this.ensureLoggedIn(failure)) { return; }

                var delete_url = this.url + 'auth/user/' + this.user_name + '/';
                var req = this.getReq('PUT', delete_url);
                req.data = {'passhash': this.getHashFromCleartext(password)};
                this.wrapHttpCall(req, success, failure);
            }
        };
    }
]);