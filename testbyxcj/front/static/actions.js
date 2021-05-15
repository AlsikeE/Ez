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
// send_to_update = function(){
//     $.post('update',)
// }
