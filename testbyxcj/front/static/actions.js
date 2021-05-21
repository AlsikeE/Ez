startall = function(){
    console.log($('#tcam').val())
    // $.get('/start_all/', {'method':'GET', 'text':'from html'}, function(data){alert(data)})
    $.post('/start_all/',{
        'tcam':$("#tcam").val(),
        'buff':$("#buff").val()
    },
    function(data){alert(data)})
}

stopall = function(){
    $.get('/stop_all/', {'method':'GET', 'text':'from html'}, function(data){alert(data)})
}

send_to_update= function(){
    console.log($("#flows").val())
    $.post('/update/',{
        'flows':$("#flows").val()
    },
    function(data){alert(data)})
}

get_methlogs = function(){
    $.get('/methlogs/', {'method':'GET', 'text':'from html'}, 
    function(data){
        // alert(data);
        $("#method_logs").val(data);

    })
}
// put_in_dom = function(some_dict,some_target){
//     len = some_dict.length
//     i = 0
//     while (i < len){
//         to_add = '<div class="row"  '
//     }

// }

get_imgs = function(){
    $.get('/imgs/',{'method':'GET','text':'from html'},
    function(data){
        var obj = JSON.parse(data)
        let bw_dict = obj.bw
        let jt_dict = obj.jitter
        let ls_dict = obj.loss
        console.log(bw_dict)
        console.log(jt_dict)
        console.log(ls_dict)
        bw_dict.forEach(function(a){
            flow_name = a.split('/').pop().replace('.png','')
            to_add = `<img src= ${a} class="img-responsive" title= ${flow_name}/>`
            $("#bwimgs").append(to_add)
        })
        jt_dict.forEach(function(a){
            flow_name = a.split('/').pop().replace('.png','')
            to_add = `<img src= ${a} class="img-responsive" title= ${flow_name}/>`
            $("#jitter").append(to_add)
        })
        ls_dict.forEach(function(a){
            flow_name = a.split('/').pop().replace('.png','')
            to_add = `<img src= ${a} class="img-responsive" title= ${flow_name}/>`
            $("#loss").append(to_add)
        })
    })
    
}
// send_to_update = function(){
//     $.post('update',)
// }
