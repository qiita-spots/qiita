/*
 *
 * This is the boring glue for the Resumable.js-based uploader.
 *
 * For the interesting stuff, see
 * http://www.23developer.com/opensource
 * http://github.com/23/resumable.js
 *
 * Steffen Tiedemann Christensen, steffen@23company.com
 *
 */

(function(window, document, $, undefined)
 {
   window.ResumableUploader = function(savedData, browseTarget, dropTarget, progressContainer, uploaderList, fileEditContainer, maxFileSize, study_id, valid_extensions, target_prefix, is_admin, url) {
     var $this = this;
     // Bootstrap parameters and clear HTML
     this.originalDocumentTitle = document.title;
     this.savedData = savedData;
     this.browseTarget = browseTarget;
     this.dropTarget = dropTarget;
     this.maxFileSize = maxFileSize;
     this.study_id = study_id;
     this.valid_extensions = valid_extensions.split(",");

     this.progressContainer = progressContainer;
     this.progressContainer.hide();

     this.uploaderList = uploaderList;
     this.uploaderList.empty();
     this.uploaderList.show();

     this.fileEditContainer = fileEditContainer;
     this.fileEditContainerHTML = fileEditContainer.html();
     this.fileEditContainer.empty();
     this.fileEditContainer.show();

     // Defaults
     this.fallbackUrl = target_prefix + '/upload/flash';
     // Properties
     this.resumable = null;
     this.progress = 0;
     this.progressPercent = 0;
     this.files = {};
     this.fileCount = 0;

     // Initialization routines
     this.bootstrapResumable = function(){
       // Build the uploader application
       this.resumable = new Resumable({
           chunkSize:3*1024*1024,
           maxFileSize:this.maxFileSize*1024*1024*1024,
           simultaneousUploads: 1,
           target:target_prefix + '/upload/',
           query:{study_id:this.study_id},
           prioritizeFirstAndLastChunk:false,
           throttleProgressCallbacks:1
         });
       if(!this.resumable.support) {
         location.href = this.fallbackUrl;
       }
       this.resumable.assignBrowse(this.browseTarget);
       this.resumable.assignDrop(this.dropTarget);

       this.resumable.on('fileError', function(file, message){
           $this.setFileUploadStatus(file.uniqueIdentifier, 'error', message);
           $this.setFileProgress(file.uniqueIdentifier, -1);
         });
       this.resumable.on('fileSuccess', function(file, message){
           $this.setFileUploadStatus(file.uniqueIdentifier, 'completed', '');
           $this.setFileProgress(file.uniqueIdentifier, 1);
         });
       this.resumable.on('fileProgress', function(file){
           $this.setFileProgress(file.uniqueIdentifier, file.progress());
           $this.setProgress($this.resumable.progress());
           // Apply a thumbnail
           if(file.chunks.length>0 && file.chunks[0].status()=='success' && file.chunks[file.chunks.length-1].status()=='success'){
             var alphaNumFileName = file.fileName.replace(/[^0-9a-z]/gi, '');
             $('#file-icon-' + alphaNumFileName).removeClass('blinking-message glyphicon-circle-arrow-up').addClass('glyphicon-ok');
             $this.setFileThumbnail(file.uniqueIdentifier, target_prefix + '/api/photo/frame?time=10&study_id='+encodeURIComponent(this.study_id)+'&resumableIdentifier='+encodeURIComponent(file.uniqueIdentifier));
           }
         });
       this.resumable.on('complete', function(file){});
       this.resumable.on('pause', function(file){
           $this.progressContainer.removeClass('is-completed');
           $this.progressContainer.addClass('is-paused');
         });
       this.resumable.on('fileRetry', function(file){});
       this.resumable.on('fileAdded', function(file){
           // Remove navigation
           $('h1, #sidebar, .bottomhelp').remove();
           $('#main').removeClass('withsidebar');
           // Handle sync
           $('#sync').hide();
           $this.resumable.opts.query['alias_sites'] = $('#alias_sites').val();
           // Add the file
           $this.addFile(file);
           // We want to upload when files are added
           $this.progressContainer.show();
           $this.resumable.upload();
         });
     }

     /* METHODS */
     this.setProgress = function(progress){
       $this.progressContainer.removeClass('is-paused is-completed');
       if(progress>=1) $this.progressContainer.addClass('is-completed');

       $this.progress = progress;
       $this.progressPercent = Math.floor(Math.floor(progress*100.0));

       document.title = '(' + $this.progressPercent + ' %) ' + $this.originalDocumentTitle;

       $this.progressContainer.find('.progress-text').html($this.progressPercent + ' %');
       $this.progressContainer.find('.progress-bar').css({width:$this.progressPercent + '%'});
     }

     // Add a new file (or rather: glue between newly added resumable files and the UI)
     this.addFile = function(resumableFile){
       // A list and and edit item for the UI
       fileName = resumableFile.fileName
       dirId = resumableFile.dirid

       // validating extensions
       is_valid = false;
       _.each(this.valid_extensions, function(extension) {
           if (extension != "" && S(fileName).endsWith(extension)) {
             is_valid = true;
             return;
           }
       })
       if (!is_valid) {
         alert('Not a valid extension: ' + fileName + '! Try again.');
         // Stop transfer - JS
         resumableFile.cancel();
         // Raise error so it doesn't go to the server - Python
         throw new Error("Not a valid extension");
       }

       var listNode = $(document.createElement('div'));
       var alphaNumFileName = fileName.replace(/[^0-9a-z]/gi, '');
       var iconClass = resumableFile.uploaded !== undefined ? 'glyphicon-ok' : 'blinking-message glyphicon-circle-arrow-up';
       var html = '<div class="row" class="checkbox">' +
                    '<label>' + fileName + '&nbsp; <input type="checkbox" value="' + dirId + '-' + fileName  + '" name="files_to_erase">&nbsp;</label>' +
                    '<i id="file-icon-' + alphaNumFileName + '" class="glyphicon ' + iconClass + '"></i>';

       if (is_admin) {
         html = html + '&nbsp;<a href="' + url + fileName + '">download</a>';
       }

       html = html + '</div>';
       listNode.html(html);
       this.uploaderList.append(listNode);

       var editNode = $(document.createElement('div'));
       editNode.html(this.fileEditContainerHTML);
       editNode.hide();
       this.fileEditContainer.append(editNode);

       // Record the new file (uploadStatus=[uploading|completed|error], editStatus=[editing|saving|saved])
       var identifier = resumableFile.uniqueIdentifier;
       if(this.savedData[identifier]) {
         var x = this.savedData[identifier];
         var editStatus = 'saved';
       } else {
         var x = {};
         var editStatus = 'editing';
       }

       var file = {
         resumableFile:resumableFile,
         listNode:listNode,
         editNode:editNode,
         fileName:resumableFile.fileName,
         title:x.title||resumableFile.fileName,
         description:x.description||'',
         tags:x.tags||'',
         published:(x.publish==1?true:false),
         album_id:x.album_id||'',
         album_label:x.album_label||'',
         editStatus:'editing',
         uploadStatus:'uploading',
         errodfpessage:'',
         thumbnailUrl:'',
         progress:0,
         progressPercent:'0 %',
         fileSize:resumableFile.size,
         fileSizeFmt:Math.round((resumableFile.size/1024.0/1024.0)*10.0)/10.0 + ' MB'
       };
       this.files[identifier] = file;
       this.fileCount++;
       this.reflectFile(identifier);
       this.reflectFileForm(identifier);

       // Attach to the form to list for updates to the file
       var showEdit = function(){
         // Show file editing
         $this.uploaderList.children().removeClass('is-active');
         $this.fileEditContainer.children().hide();
         listNode.addClass('is-active');
         editNode.show();
       }
       listNode.click(showEdit);
       if(this.fileCount==1) showEdit(); // Activate editing for the first file


      // qiita: ===> This is currently not needed but we might need it in the future
      //  editNode.find('form').submit(function(e){
      //      // Save data to object
      //      var form = $(e.target);
      //      file.title = form.find('.file-edit-form-title input').val();
      //      file.description = form.find('.file-edit-form-description textarea').val();
      //      file.tags = form.find('.file-edit-form-tags input[name=tags]').val();
      //      form.find('.file-edit-form-album select').each(function(i,select){
      //          file.album_id = $(select).val();
      //          file.album_label = select.options[select.selectedIndex].label;
      //        })
      //      file.published = form[0].published_p.checked;
      //
      //      // Save the data through API
      //      file.editStatus = 'saving';
      //      $this.reflectFile(identifier);
      //      var data = {
      //        study_id:this.study_id,
      //        resumableIdentifier:identifier,
      //        title:file.title||'',
      //        description:file.description||'',
      //        album_id:file.album_id||'',
      //        album_label:file.album_label||'',
      //        tags:file.tags||'',
      //        publish:(file.published ? 1 : 0)
      //      };
      //      $.ajax('/api/photo/update-upload-token', {type:'POST', data:data, success:function(){
      //            file.editStatus = 'saved';
      //            $this.reflectFile(identifier);
      //          }});
      //
      //      return false;
      //    });
      //
      //  editNode.find('input.file-edit-edit').click(function(e){
      //      // Edit file
      //      file.editStatus = 'editing';
      //      $this.reflectFile(identifier);
      //    });
      //
      //  editNode.find('a.file-edit-cancel').click(function(e){
      //      // Cancel upload
      //      $this.removeFile(identifier);
      //      if($this.fileCount<=0) $this.progressContainer.hide();
      //
      //      return false;
      //    });
     }

     // Cancel a file an remove the
     this.removeFile = function(identifier){
       if(!this.files[identifier]) return;
       var f = this.files[identifier];

       this.uploaderList[0].removeChild(f.listNode[0]);
       this.fileEditContainer[0].removeChild(f.editNode[0]);
       f.resumableFile.cancel();
       delete this.files[identifier];
       this.fileCount--;
     }

     // Update for the file
     this.reflectFileForm = function(identifier){
       if(!this.files[identifier]) return;
       var f = this.files[identifier];

       var form = f.editNode.find('form')[0];
       f.editNode.find('.file-edit-form-title input').val("This is the title");
       f.editNode.find('.file-edit-form-description textarea').val("This is the descrition");
       f.editNode.find('.file-edit-form-tags input').val("These are tags");
       f.editNode.find('.file-edit-form-album select').val("My albums");
     }

     // Update UI to reflect the status of the object
     this.reflectFile = function(identifier){
       if(!this.files[identifier]) return;
       var f = this.files[identifier];

       var allStatusClasses = 'is-uploading is-completed is-error is-editing is-saving is-saved';

       // List
       f.listNode.find('.uploader-item-title').html(f.title);
       f.listNode.removeClass(allStatusClasses)
       f.listNode.addClass(['is-'+f.uploadStatus, 'is-'+f.editStatus].join(' '));

       // Edit
       f.editNode.find('.file-edit-meta-size span').html(f.fileSizeFmt);
       f.editNode.find('.file-edit-meta-filename span').html(f.fileName);
       f.editNode.removeClass(allStatusClasses)
       f.editNode.addClass(['is-'+f.uploadStatus, 'is-'+f.editStatus].join(' '));
       if(f.editStatus=='saved') {
         try {
           var d = f.description.replace(/<\/?[^>]+>/gi, '');
           if(d.length>360) d = d.substr(0,360) + '...';
         }catch(e){alert(e); var d = '';}
         jQuery.each({
             'file-edit-form-title':f.title,
             'file-edit-form-description':d,
             'file-edit-form-tags':f.tags,
             'file-edit-form-album':f.album_label
           }, function(className,text){
             f.editNode.find('.file-edit-form-saved .' + className + ' .file-edit-form-widget').html(text);
             f.editNode.find('.file-edit-form-saved .' + className + ' .file-edit-form-widget').css({display:(text.length>0 ? 'block' : 'none')});
             f.editNode.find('.file-edit-form-saved .' + className + ' .file-edit-form-widget-empty').css({display:(text.length>0 ? 'none' : 'block')});
           });
         f.editNode.find('.file-edit-form-saved .file-edit-form-widget-publish').css({display:(f.published?'block':'none')});
         f.editNode.find('.file-edit-form-saved .file-edit-form-widget-nopublish').css({display:(f.published?'none':'block')});
       }

       // Error
       f.editNode.find('.file-edit-error h2, .file-edit-error b').html(f.fileName);
     }

     // Update file with thumbnails
     this.setFileThumbnail = function(identifier, url){
       if(!this.files[identifier] || this.files[identifier].thumbnailUrl.length>0) return;
       url+='&_='+Math.random()
       this.files[identifier].thumbnailUrl = url;
       this.files[identifier].listNode.find('img.uploader-item-thumbnail').each(function(i,img){
           $(img).attr('src', url);
         });
       this.files[identifier].editNode.find('img.file-edit-thumbnail').each(function(i,img){
           $(img).attr('src', url);
         });
     }

     // Update file progress
     this.setFileProgress = function(identifier, progress){
       if(!this.files[identifier]) return;
       var f = this.files[identifier];

       f.progress = progress;
       f.progressPercent = Math.floor(Math.round(progress*100.0));

       // Update the percent indication
       f.editNode.find('.file-edit-meta-progress-processing span').html(f.progressPercent + ' %');
       f.editNode.find('.file-edit-meta-progress-processing').css({display:(f.uploadStatus!='error' && (f.uploadStatus!='complete' && progress<1) ? 'block' : 'none')});
       f.editNode.find('.file-edit-meta-progress-complete').css({display:(f.uploadStatus!='error' && (f.uploadStatus=='complete'||progress>=1) ? 'block' : 'none')});
       f.editNode.find('.file-edit-meta-progress-complete span a').attr('href', '/actions?action=resumable-upload-redirect&study_id='+encodeURIComponent(this.study_id)+'&resumableIdentifier='+encodeURIComponent(identifier));

       // Update progress icon
       f.listNode.find('img.uploader-item-status').each(function(i,img){
           $(img).attr('src', (f.uploadStatus=='error' ? '/resources/um/graphics/uploader/error.png' : (f.uploadStatus=='complete'||progress>=1 ? '/resources/um/graphics/uploader/done.png' : '/resources/um/graphics/uploader/uploaded-'+(Math.floor(progress*10.0)*10.0)+'.png')));
         });
     }

     // Update file upload status
     this.setFileUploadStatus = function(identifier, uploadStatus, errorMessage){
       if(!this.files[identifier]) return;
       this.files[identifier].uploadStatus = uploadStatus;
       this.files[identifier].errorMessage = errorMessage;
       $this.reflectFile(identifier);
     }

     // Init for real
     this.bootstrapResumable();
     return this;
   }
 })(window, window.document, jQuery);
