/**
 *
 * @author Daniel McDonald
 * @copyright Copyright 2014, biocore
 * @credits Daniel McDonald, Joshua Shorenstein, Jose Navas
 * @license BSD
 * @version 0.1.0-dev
 * @maintainer Daniel McDonald
 * @email mcdonadt@colorado.edu
 * @status Development
 *
 */

/**
 *
 * @name moi
 *
 * @class manages WebSocket for job and group information
 *
 */
var moi = new function () {
    this.VERSION = '0.1.0-dev';

    var
      /* the server end of the websocket */
      host = 'ws://' + window.location.host + '/moi-ws/',
      
      /* the websocket */     
      ws = null,

      /* registered callbacks */
      callbacks = {},

      /* the encode and decode methods used for communication */
      encode = JSON.stringify,
      decode = JSON.parse;

    /**
     *
     * Registers a callback method for a given action
     *
     * @param {action} The associated action verb, str. 
     * @param {func} The associated function, function. This function must 
     * accept an object. Any return is ignored. 
     *
     */
    this.add_callback = function(action, func) {callbacks[action] = func};

    /**
     *
     * Packages data into an object, and passes an encoded version of the 
     * object to the websocket.
     *
     * @param {action} The associated action to send, str.
     * @param {data} The data to send, str or Array of str.
     */
    this.send = function(action, data) {
        to_send = {}; 
        to_send[action] = data;
        ws.send(encode(to_send))
    };
    
    /**
     *
     * Verify the browser supports websockets, and if so, initialize the
     * websocket. On construction, this method will send a message over the
     * socket to get all known job information associated with this client.
     */
    this.init = function() {
        if (!("WebSocket" in window)) {
            alert("Your browser does not appear to support websockets!");
            return;
        }
        ws = new WebSocket(host);

        ws.onopen = function() {ws.send(encode({"get": []}))};
        ws.onclose = function(evt) {ws.send(encode({"close": null}))};
        ws.onerror = function(evt) {};

        ws.onmessage = function(evt) {
            message = decode(evt.data);
            for(var action in message) 
                if(action in callbacks) 
                    callbacks[action](message[action]);
        };
    };
};
