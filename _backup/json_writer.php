<?php
// strip slashes before putting the form data into target file
$val = $_GET['val'];


// if the code string is not empty then open the target file and put form data in it
    $filename = "dailyCons_1.json";
     $file = fopen($filename, "w");
    //echo fwrite($file, $cd);
    fwrite($file, $val);
    // show a success msg 
    fclose($file);
    echo "Json ",  $val, " erfolgreich geschrieben";
    


?>
