<?php
// strip slashes before putting the form data into target file
$val = $_GET['val'];


// if the code string is not empty then open the target file and put form data in it
    $filename = "dailyCons_1.json";
    $file = fopen($filename, "r");
    //echo fwrite($file, $cd);
    $content = fread($file, filesize($filename));
    // show a success msg 
    fclose($file);
    echo $content;

?>
