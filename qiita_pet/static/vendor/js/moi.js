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
      host = null,
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
    this.add_callback = function(action, func) { callbacks[action] = func; };

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
        ws.send(encode(to_send));
    };

    /**
     *
     * Verify the browser supports websockets, and if so, initialize the
     * websocket. On construction, this method will send a message over the
     * socket to get all known job information associated with this client.
     *
     * @param {host} The URL for the websocket, minus the ws:// header, or null
     * to use the default moi-ws.
     * @param {group_id} A group ID to get initial data from, or null to fetch
     * all records associated with the user.
     * @param {on_open} Optional function for action when websocket is opened.
     * @param {on_close} Optional function for action when websocket is closed.
     * @param {on_error} Optional function for action when websocket errors.
     */
    this.init = function(group_id, host, on_open, on_close, on_error) {
        host = host || window.location.host + '/moi-ws/';
        if (!("WebSocket" in window)) {
            alert("Your browser does not appear to support websockets!");
            return;
        }
        //check if we need regular or secure websocket
        socket = window.location.protocol == "https:" ? 'wss://' : 'ws://';
        ws = new WebSocket(socket + host);

        var on_open_message = null;
        if (group_id === null) {
            on_open_message = [];
        } else {
            on_open_message = [group_id];
        }

        on_open = on_open || function() { ws.send(encode({"get": on_open_message})); };
        on_close = on_close || function(evt) { ws.send(encode({"close": null})); };
        on_error = on_error || function(evt) {};

        ws.onopen = on_open;
        ws.onclose = on_close;
        ws.onerror = on_error;

        ws.onmessage = function(evt) {
            message = decode(evt.data);
            for(var action in message) {
                if(action in callbacks) {
                    callbacks[action](message[action]);
                }
            }
        };
    };
};
