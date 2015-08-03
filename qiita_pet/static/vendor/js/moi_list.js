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

var moi_list = new function () {
    var info_ids = {};
    var info_list = null;
    var restrict_to_group_id = null;

    function createButton(context, func){
        var button = document.createElement("input");
        button.type = "button";
        button.value = "Remove";
        button.onclick = function () { func(context.getAttribute("id")) };
        context.appendChild(button);
    };


    function tracked_node(info) {
        return restrict_to_group_id == info['parent'];
    };


    function setResult(info) {
        if(!tracked_node(info))
            return;

        var results = document.createElement("a");
        results.href = info.url + '/' + info.id;
        results.innerHTML = info.status;

        var state_node = document.getElementById(info.id + ":status");
        var para_node = state_node.parentNode;
        var remove_node = para_node.lastChild;
        
        para_node.insertBefore(results, remove_node);
        para_node.removeChild(state_node); 
    };


    function addInfo(info) {
        if(!tracked_node(info))
            return;

        if(info.id in info_ids) 
            return;

        var para = document.createElement("p");
        para.setAttribute("id", info.id);
        var para_node = document.createTextNode(info.name + ': ');
        
        var state = document.createElement("span");
        state.setAttribute("id", info.id + ":status");
        
        if(info.type == 'job') {   
            var state_node = document.createTextNode(info.status);
        } else { 
            var state_node = document.createElement("a");
            state_node.href = info.url + '/' + info.id;
            state_node.innerHTML = 'Group details';
        }

        para.appendChild(para_node);
        state.appendChild(state_node);
        para.appendChild(state);
        createButton(para, function (id_to_drop) {  
                                          moi.send("remove", [id_to_drop]); 
                                          removeInfo(id_to_drop);
                                      }); 
        info_list.appendChild(para);
       
        if(info.type == 'job') { 
            if((info.status == 'Success' || info.status == 'Failed') && info.url) { 
                setResult(info);
            }
        }
        
        info_ids[info.id] = para;
    };

    function removeInfo(id) {
        // can't get here without the user clicking so tracking isn't relevant
        if(id in info_ids) {
            para_node = info_ids[id]; 
            info_list.removeChild(para_node);
            delete info_ids[id];
        }
    };

    function updateInfo(info) {
        if(!tracked_node(info))
            return;

        if((info.status == 'Success' || info.status == 'Failed') && info.url) { 
            setResult(info);
        }
        else {
            status_msg = document.getElementById(info.id + ":status");
            
            if (!(status_msg == null)) {
                // if a result has been set, then the status is no more
                status_msg.innerHTML = info.status;
            }
        }
    };

    this.init = function (group_id, div) {
        if (typeof div === 'undefined') {
            div = document.body;
        }

        restrict_to_group_id = group_id;
        info_list = document.createElement("div");
        info_list.setAttribute("id", "moi-list");
        div.appendChild(info_list);
        
        moi.add_callback('add', addInfo);
        moi.add_callback('get', addInfo);
        moi.add_callback('remove', removeInfo);
        moi.add_callback('update', updateInfo);
        moi.init(group_id);
    };
};
