$(function() {
  $('#clear').on('click', function() {
    $('#search-query').val('');
    $('#search-results').hide();
  });

  $('#search-button').on('click', function() {
    return search();
  });
  
  $('#search-query').on('keyup', function() {
    return search();
  });

  function search() {
    var query   = $('#search-query').val();
    var result  = $('#search-results');
    var entries = $('#search-results .entries');

    if (query.length <= 2) {
      result.hide();
      entries.empty();
    } else {
      // retrieve matching result with content
      var results = $.map(idx.search(query), function(result) {
        return $.grep(docs, function(entry) {
          return entry.id === result.ref;
        })[0];
      });

      entries.empty();

      if (results && results.length > 0) {
        $.each(results, function(key, nom) {
          entries.append(
          '  <h4>'+
          '    <a href="/nom/'+nom.id+'">'+nom.c+'<span class="pull-right">'+nom.k+'</span></a>'+
          '  </h4>');
        });
      } else {
        entries.append('<h4>Không tìm thấy chữ :-(</h4>');
      }

      result.show();
    }

    return false;
  }
});
